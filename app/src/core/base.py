from app.utils.ascii_art import ASCII_ART
from app.utils.constants import RECURSION_LIMIT, PROMPTS
from app.src.core.exception_handler import AgentExceptionHandler
from app.src.core.permissions import PermissionDeniedException
from app.src.embeddings.rag_errors import SetupFailedError, DBAccessError
from collections import Counter
import shlex
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage
from app.src.embeddings.db_client import DataBaseClient
from langgraph.graph.state import CompiledStateGraph
from typing import Callable
from langgraph.graph import StateGraph
from app.src.core.ui import AgentUI
import langgraph.errors as lg_errors
from app.utils.ui_messages import UI_MESSAGES
import uuid
import os
import openai
import re
import sys
import io

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except:
            pass  # Fallback if wrapping fails


# ============================================================================
# HELPER FUNCTIONS FOR RAG QUERY GENERATION AND RESULT FILTERING
# ============================================================================

_STOPWORDS = {
    "the","a","an","is","are","was","were","in","on","for","and","or","of","to","with","by",
    "this","that","these","those","how","what","why","when","where","who","which"
}

_UI_NOISE_PATTERNS = [
    r'^\s*important[:\s]', r'^\s*always[:\s]', r'^\s*note[:\s]', r'^[\\/A-Za-z]:\\', r'^\s*█+',
    r'^\s*╭', r'^\s*╰', r'^\s*—+', r'^\s*━+'
]
_GENERIC_NOISE = {"important","always","note","please","thanks","ok","im","i'm","imho","ciao"}


def _clean_user_input_for_queries(raw: str) -> str:
    """Remove UI banners, paths, and obvious noise that sometimes get included in prompt text."""
    lines = []
    for line in raw.splitlines():
        ln = line.strip()
        if not ln:
            continue
        # drop lines that match obvious UI/title noise
        if any(re.search(pat, ln, re.IGNORECASE) for pat in _UI_NOISE_PATTERNS):
            continue
        # drop short one/two word lines that are clearly UI or headings
        if len(ln.split()) <= 2 and ln.lower() in _GENERIC_NOISE:
            continue
        # drop lines that look like "C:\AI-Projects\..."
        if re.search(r'[A-Za-z]:\\', ln):
            continue
        lines.append(ln)
    return " ".join(lines).strip()


def generate_search_queries(user_input: str, max_queries: int = 4) -> list[str]:
    """Generate short, sensible search queries from user input.
    Avoid one-word generic queries like 'Is' by prioritizing proper nouns and long tokens.
    """
    ui = _clean_user_input_for_queries(user_input).strip()
    if not ui:
        ui = user_input.strip()  # fallback if cleaning removed everything
    queries = []
    
    # 1) Find capitalized multiword proper nouns (e.g., 'Shai Gilgeous-Alexander', 'IDW')
    proper_nouns = re.findall(r'\b([A-Z][a-zA-Z0-9\-]{2,}(?:\s+[A-Z][a-zA-Z0-9\-]{2,})*)\b', ui)
    
    # 2) Single capitalized tokens (may include acronyms)
    caps = re.findall(r'\b([A-Z]{2,}|[A-Z][a-z]{3,})\b', ui)
    
    # 3) Long lowercase tokens (meaningful words)
    tokens = re.findall(r'\b([a-z0-9]{4,})\b', ui.lower())
    tokens = [t for t in tokens if t not in _STOPWORDS]
    
    # Prioritize multiword proper nouns with context
    for pn in proper_nouns:
        if len(pn) > 4 or pn.isupper():  # Real proper noun or acronym
            queries.append(pn)
            if len(queries) >= max_queries:
                return queries
    
    # Add single capitalized terms that aren't already captured
    for c in caps:
        c_lower = c.lower()
        if c_lower not in tokens and c_lower not in [q.lower() for q in queries]:
            queries.append(c)
            if len(queries) >= max_queries:
                return queries
    
    # Add top meaningful tokens by frequency
    token_freq = Counter(tokens)
    for t, freq in token_freq.most_common():
        if t not in [q.lower() for q in queries]:
            queries.append(t)
            if len(queries) >= max_queries:
                return queries
    
    # Safety: remove any extremely short or generic queries
    queries = [q for q in queries if len(q) >= 3 and len(re.findall(r'[A-Za-z0-9]{2,}', q)) >= 1]
    
    if not queries:
        # Last resort: return first few meaningful words from input
        words = re.findall(r'\b[A-Za-z0-9]{3,}\b', ui)
        words = [w for w in words if w.lower() not in _STOPWORDS]
        return words[:max_queries] if words else [ui[:100]]
    
    return queries[:max_queries]


def build_relevance_keywords(user_input: str, search_queries: list[str]) -> list[str]:
    """Return cleaned, deduplicated keywords used to score results."""
    words = []
    # extract nouns/proper tokens from user_input and queries
    for s in [user_input] + search_queries:
        for w in re.findall(r'\b[A-Za-z0-9\-]{3,}\b', s):
            lw = w.lower()
            if lw in _STOPWORDS:
                continue
            if lw.isdigit():
                continue
            words.append(lw)
    # prioritize unique and longer tokens first
    ks = sorted(set(words), key=lambda x: (-len(x), x))
    return ks[:20]


def validate_search_results(results: list[dict], relevance_keywords: list[str]) -> list[dict]:
    """Drop obviously irrelevant results (titles/snippets not containing keywords or are generic pages).
    Returns filtered list preserving order. Avoids any hardcoded name checks.
    """
    filtered = []
    # normalize keywords to lowercase for substring checks
    kw_set = {k.lower() for k in (relevance_keywords or [])}

    for r in results:
        title = (r.get("title") or "").strip()
        snippet = (r.get("snippet") or r.get("summary") or "").strip()
        combined = (title + " " + snippet).lower()

        # reject extremely short or meaningless titles like "Is" or single-letter garbage
        if not title or re.fullmatch(r'[a-z]{1,3}', title.strip().lower()):
            continue

        # if any relevance keyword is a substring of the combined text, accept
        has_kw = any(kw in combined for kw in list(kw_set)[:10])  # check top keywords first

        # else: accept if title contains a multi-word Proper Noun phrase (e.g., "Shai Gilgeous-Alexander")
        title_proper_phrases = re.findall(r'\b([A-Z][a-zA-Z0-9\-]{2,}(?:\s+[A-Z][a-zA-Z0-9\-]{2,})+)\b', title + " " + snippet)
        has_proper_overlap = False
        for phrase in title_proper_phrases:
            # if any token of the detected proper phrase appears in our relevance keywords, treat as match
            for token in re.findall(r"[A-Za-z0-9\-]{3,}", phrase):
                if token.lower() in kw_set:
                    has_proper_overlap = True
                    break
            if has_proper_overlap:
                break

        if has_kw or has_proper_overlap:
            filtered.append(r)

    return filtered


def needs_research(user_input: str, force_research: bool | None = None) -> bool:
    """Decision helper. Forces research when fictional universes or named characters appear.
    Otherwise uses heuristics (question words, 'compare', 'latest', years, stats, person discussions).
    Provide a force_research override (True/False/None).
    """
    if force_research is True:
        return True
    if force_research is False:
        return False

    ui = user_input.lower()
    # If the user explicitly mentions a fictional universe or proper-noun-heavy comparison, research
    fiction_markers = ['idw', 'transformer', 'transformers', 'comic', 'marvel', 'dc', 'universe', 'megatron']
    if any(m in ui for m in fiction_markers):
        return True

    heur_keys = [
        r'\b(latest|recent|today|yesterday|this week|this month|202[0-9]|[0-9]{4})\b',
        r'\b(stat|percent|percentage|how many|count|number|rate|freethrow|free throw|foul)\b',
        r'\b(compare|vs|versus|difference|similar to|like|analog)\b',
        r'\b(who|when|where|which|what year|why)\b',
        r'\b(news|announce|report|study|survey|research)\b',
        r'(has been|been|is|was|were)\s+(treated|portrayed|described|shown|claimed|promoted|criticized|attacked)',
    ]
    for p in heur_keys:
        if re.search(p, ui):
            return True
    return False


def duckduckgo_search_fallback(query: str, max_results: int = 10, timeout: int = 8) -> list[dict]:
    """
    Lightweight fallback that queries DuckDuckGo's HTML endpoint and scrapes result links.
    Returns list of dicts with keys: 'title', 'link', 'snippet' (snippet may be empty).
    Uses `requests` if available; otherwise raises ImportError.
    """
    try:
        import requests
    except Exception as e:
        raise ImportError("requests not available for fallback duckduckgo search") from e

    url = "https://html.duckduckgo.com/html/"
    payload = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RAG-Fallback/1.0)"}

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=timeout)
        html = resp.text
    except Exception as e:
        raise RuntimeError(f"DuckDuckGo HTML fetch failed: {e}") from e

    # crude extraction of result anchors and titles
    # match href="https://..." occurrences
    links = []
    for m in re.finditer(r'href="(https?://[^"]+)"', html):
        link = m.group(1)
        # skip duckduckgo internal links
        if "duckduckgo.com" in link:
            continue
        links.append(link)

    # dedupe while preserving order
    seen = set()
    outputs = []
    for link in links:
        if link in seen:
            continue
        seen.add(link)
        # try to extract title by finding the anchor text nearby (fallback to link as title)
        title_match = re.search(rf'<a[^>]+href="{re.escape(link)}"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
        title = re.sub(r'<.*?>', '', title_match.group(1)).strip() if title_match else link
        outputs.append({"title": title, "link": link, "snippet": ""})
        if len(outputs) >= max_results:
            break

    return outputs


def build_kb_only_prompt(user_input: str, kb_context: str) -> str:
    """
    Strict KB-only prompt: require explicit evidence. If KB lacks direct evidence for
    statistics or recent articles, the model must say so and provide exact search queries
    for verification.
    """
    prompt = [
        "You are given: (A) a user's question, and (B) internal knowledge-base context from stored documents.",
        "Task: Provide a short, clear analytic answer grounded ONLY in the KB. Do NOT introduce external authors or analogies unless they are explicitly cited in the KB.",
        "RULES:",
        "  1) Start with a 2-3 sentence thesis that answers the user's question directly and states whether the KB contains direct supporting evidence (yes/no).",
        "  2) Provide up to three supporting points. For each point, explicitly cite the KB source (e.g., [KB: filename]) and quote or paraphrase the supporting sentence. If no KB evidence exists for a point, write 'no direct KB evidence'.",
        "  3) If numerical/statistical claims (e.g., free throws, attempts, per-game averages) are relevant, include the exact numeric values and the KB citation. If the KB does not contain numbers, say 'no numeric data in KB' and add a precise web search query the user can run.",
        "  4) Do not invent or attribute ideas to Malcolm X, Parenti, Du Bois, or other thinkers unless those names are present in the KB and cited. If you draw an analogy, label it 'ANALOGY' and explain why it might help, but make clear it is not KB fact.",
        "  5) End with one 1-sentence limitation and then list up to three suggested exact web search queries the user can run to collect missing evidence (each query on its own line).",
        "",
        "KB CONTEXT (begin):",
        kb_context[:9000],
        "KB CONTEXT (end).",
        "",
        f"USER QUESTION: {user_input}",
        "",
        "Answer now following the RULES above."
    ]
    return "\n".join(prompt)


class BaseAgent:
    """Base class for all agent implementations.

    Provides common functionality including chat interface, model management,
    and message handling for agent interactions.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str,
        system_prompt: str,
        agent: CompiledStateGraph,
        ui: AgentUI,
        get_agent: Callable,
        temperature: float = 0,
        graph: StateGraph = None,
        provider: str = None,
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.agent = agent
        self.ui = ui
        self.get_agent = get_agent
        self.temperature = temperature
        self.graph = graph
        self.provider = provider

        # a dictionary to hold custom command names and handlers
        self._custom_commands: dict[str, Callable] = {}

        # a flag to determine if RAG features should be integrated
        self.rag = False

        self.latest_refs: set[str] = set()
        self.db_client = None
        
        # Research decision override: None = auto, True = always research, False = never research
        self.force_research: None | bool = None
        
        # Track current response for Stage 1/2 accumulation
        self._current_response = ""
        
        # Track token usage for context window management
        self._stage1_tokens = 0
        self._stage2_tokens = 0

        # backup model name after failed `/model change` command
        self.prev_model_name = None

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for context window tracking.
        Uses simple estimation: ~4 characters per token (approximation for qwen2.5).
        More accurate: use actual tokenizer, but this works for rough estimates.
        """
        return max(1, len(text.strip()) // 4)

    def _build_relevance_keywords(self, user_input: str, enhanced_query: str) -> list[str]:
        """Derive topic-specific relevance terms from the user's prompt and search query.
        This version auto-detects proper nouns and high-value tokens rather than hardcoding names.
        """
        text = f"{user_input} {enhanced_query}".strip()
        lower_text = text.lower()
        # grab tokens (letters/numbers/') with length >=3
        tokens = re.findall(r"[a-z0-9']{3,}", lower_text)

        stop_words = {
            "the","and","for","with","that","this","from","about","into","have","has","was","were",
            "are","been","their","there","which","when","your","you","they","them","she","him","his",
            "her","not","but","can","will","just","like","into","than","is","a","an","of","to","in","on"
        }

        # frequency-based keywords (lowercase)
        freq = Counter(t for t in tokens if t not in stop_words)
        keywords = [w for w, _ in freq.most_common(12)]

        # Fallback to non-trivial tokens if frequency collapsed
        if not keywords:
            keywords = [t for t in tokens if len(t) > 4][:8]

        # Detect proper-noun phrases from the original-cased text (e.g., "Shai Gilgeous-Alexander")
        proper_phrases = re.findall(r'\b([A-Z][a-zA-Z0-9\-]{2,}(?:\s+[A-Z][a-zA-Z0-9\-]{2,})*)\b', text)
        for pp in proper_phrases:
            pp_clean = pp.strip()
            pp_lower = pp_clean.lower()
            if pp_lower not in keywords:
                # split multiword proper nouns into tokens also (so they match in snippets/titles)
                keywords.insert(0, pp_lower)

        # dedupe while preserving order and limit
        seen = set()
        final = []
        for k in keywords:
            if k and k not in seen:
                seen.add(k)
                final.append(k)
            if len(final) >= 20:
                break

        return final[:20]

    def _smart_extract_facts(self, content: str, max_facts: int = 5, relevance_keywords: list[str] | None = None) -> list[str]:
        """Generic fact extractor guided by relevance keywords derived from the prompt.
        Returns prioritized short sentences useful as 'facts' for citation.
        """
        if not content:
            return []

        relevance_keywords = relevance_keywords or []
        sentences = re.split(r'(?<=[.!?])\s+', content[:5000])
        scored = []

        for sent in sentences:
            s = sent.strip()
            if len(s) < 40 or len(s) > 500:
                continue

            score = 0
            # prefer sentences containing a relevance keyword
            for kw in relevance_keywords:
                if kw and kw.lower() in s.lower():
                    score += 5
            # prefer sentences with dates, numbers, proper nouns
            if re.search(r'\b(19|20)\d{2}\b', s):
                score += 3
            if re.search(r'\b\d+%|\$\d+|\d+\b', s):
                score += 2
            if re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', s):
                score += 1
            # baseline length weight
            score += min(3, len(s) // 120)

            if score > 0:
                scored.append((score, s))

        # sort by score desc then length desc
        scored.sort(key=lambda x: (x[0], len(x[1])), reverse=True)

        facts = []
        seen = set()
        for _, s in scored:
            sl = s.lower()
            if sl in seen:
                continue
            facts.append(s)
            seen.add(sl)
            if len(facts) >= max_facts:
                break

        # fallback: pick the first few longish sentences
        if len(facts) < max_facts:
            for s in sentences:
                s = s.strip()
                if 40 < len(s) < 250 and s.lower() not in seen:
                    facts.append(s)
                    seen.add(s.lower())
                    if len(facts) >= max_facts:
                        break
        return facts

    def _extract_key_facts_from_results(self, results: list[tuple], user_input: str) -> str:
        """Pre-extract specific, substantive facts from each result with citation markers.
        This is flexible and will pull up to max_facts per result using relevance keywords derived from the user input.
        """
        if not results:
            return ""

        # build simple relevance keywords from the user input
        relevance_keywords = self._build_relevance_keywords(user_input, "")
        fact_summary = "\n" + "█"*60 + "\n"
        fact_summary += "EXTRACTED FACTS FROM WEB RESULTS\n"
        fact_summary += "█"*60 + "\n\n"

        total_fact_count = 0
        for i, (result, content) in enumerate(results[:6], 1):
            title = result.get("title", "Untitled")
            link = result.get("link", "Unknown")
            fact_summary += f"--- WEB RESULT {i}: {title} ({link}) ---\n"
            extracted = self._smart_extract_facts(content, max_facts=4, relevance_keywords=relevance_keywords)
            if not extracted:
                fact_summary += "  (no strong facts automatically extracted)\n\n"
                continue
            for fact in extracted:
                total_fact_count += 1
                fact_display = fact if len(fact) <= 300 else fact[:297] + "..."
                fact_summary += f"  [{total_fact_count}] \"{fact_display}\"\n"
            fact_summary += "\n"

        fact_summary += "█"*60 + "\n"
        fact_summary += f"TOTAL FACTS AVAILABLE (approx): {total_fact_count}\n"
        fact_summary += "█"*60 + "\n\n"

        return fact_summary

    def _compress_source_content(self, content: str, max_chars: int = 3000) -> str:
        """Compress document by keeping key sections to fit context window."""
        if len(content) <= max_chars:
            return content
        
        # Keep first portion (context)
        first = content[:1500]
        # Keep last portion (conclusion)
        last = content[-800:] if len(content) > 800 else ""
        # Extract key middle sentences (prioritize those with numbers, quotes, or substantive content)
        middle_text = content[1500:-800] if len(content) > 2300 else ""
        middle_sentences = [s.strip() for s in middle_text.split('.') if len(s.strip()) > 50]
        # Prioritize sentences with evidence markers or substantive content
        key_sentences = [s for s in middle_sentences[:5] 
                        if any(marker in s.lower() 
                               for marker in ['said', 'found', 'research', 'study', 'data', 'percent', 'showed', 'evidence', 'according'])]
        middle = '. '.join(key_sentences[:3]) if key_sentences else (middle_sentences[0] if middle_sentences else "")
        
        compressed = f"{first}\n[... COMPRESSED ...]{middle}\n{last}"
        return compressed if len(compressed) <= max_chars else compressed[:max_chars]
    
    def _extract_source_citation(self, file_path: str) -> tuple:
        """Extract author and title from file path for proper citation formatting."""
        from pathlib import Path

        p = Path(file_path)
        basename = p.stem if p.stem else p.name
        basename = basename.replace('_', ' ').strip()

        # Try format: "Title -- Author, Name"
        if ' -- ' in basename:
            parts = basename.rsplit(' -- ', 1)
            title = parts[0].strip()
            author = parts[1].strip()
            return (author, title)
        # Try format: "Author - Title"
        elif ' - ' in basename:
            parts = basename.split(' - ', 1)
            author = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
            return (author, title)
        else:
            # default: treat basename as title and unknown author
            return ("Unknown", basename)
    
    def _format_sources_with_citations(self, query_results: list) -> dict:
        """Format knowledge base sources with proper author/title citations and compression."""
        formatted_sources = []
        unique_authors = set()
        
        for i, (doc, meta) in enumerate(query_results, 1):
            file_path = meta.get("file_path", "Unknown")
            author, title = self._extract_source_citation(file_path)
            
            # Enforce source diversity
            author_key = author.split(',')[0] if ',' in author else author
            if author_key in unique_authors and len(formatted_sources) >= 3:
                continue  # Skip duplicate authors
            unique_authors.add(author_key)
            
            # Compress doc to fit context window
            compressed_doc = self._compress_source_content(doc, 2000)
            
            citation = f"[{author} - {title}]"
            formatted_sources.append({
                'index': i,
                'citation': citation,
                'author': author,
                'title': title,
                'content': compressed_doc,
                'file_path': file_path
            })
        
        return {'sources': formatted_sources, 'unique_authors': unique_authors}

    def _toggle_rag(self, enable: bool = True):
        """Enable or disable RAG features."""
        self.rag = enable

    def get_session_id(self) -> str:
        """Get the current session/thread ID."""
        return self.configuration.get("configurable", {}).get("thread_id", "")

    def _build_stage1_message(self, user_input: str, web_sources_block: str) -> tuple[str, int]:
        """Return stage1 message (and token estimate) given user question and collected web sources text."""
        stage1 = []
        stage1.append("!"*80)
        stage1.append("STAGE 1: EXTRACT DETAILED CONTEXT FROM WEB SOURCES")
        stage1.append("!"*80)
        stage1.append("")
        stage1.append("YOUR TASK: Read the web sources and extract specific, verifiable details relevant to the question.")
        stage1.append("GUIDELINES:")
        stage1.append("  - Identify entities, dates, events, and direct quotes from sources.")
        stage1.append("  - For each fact include a short citation: (From [title/URL]: \"quote or paraphrase\")")
        stage1.append("  - Emphasize sequences, motivations, and comparisons explicitly stated in sources.")
        stage1.append("")
        stage1.append("="*60)
        stage1.append("WEB SOURCES - BEGIN")
        stage1.append("="*60)
        stage1.append(web_sources_block)
        stage1.append("="*60)
        stage1.append(f"QUESTION: {user_input}")
        stage1.append("="*60)
        stage1.append("RESPOND WITH DETAILED CONTEXT FROM SOURCES. USE DIRECT QUOTES WHERE AVAILABLE.")
        full = "\n".join(stage1)
        return full, self._estimate_tokens(full)

    def _build_stage2_message(self, user_input: str, stage1_response: str, extra_rag_context: str) -> tuple[str, int]:
        """Return stage2 message that asks the model to synthesize stage1 output with KB concepts."""
        stage2 = []
        stage2.append("="*80)
        stage2.append("STAGE 2: SYNTHESIZE WITH KNOWLEDGE BASE / THEORY")
        stage2.append("="*80)
        stage2.append("ORIGINAL QUESTION:")
        stage2.append(user_input)
        stage2.append("")
        stage2.append("Stage 1 Findings:")
        stage2.append(stage1_response[:4000])  # include a slice to avoid huge context explosion
        stage2.append("")
        stage2.append("KNOWLEDGE BASE CONTEXT:")
        stage2.append(extra_rag_context)
        stage2.append("")
        stage2.append("TASK:")
        stage2.append("  - Apply the KB concepts to explain mechanisms and root causes found in Stage 1.")
        stage2.append("  - Do NOT invent parallels; rely on explicit mechanisms and documented comparisons.")
        stage2.append("  - Provide a concise final answer and a short list of supporting source citations.")
        full = "\n".join(stage2)
        return full, self._estimate_tokens(full)

    def start_chat(
        self,
        starting_msg: str = None,
        initial_prompt_suffix: str = None,
        recurring_prompt_suffix: str = None,
        recursion_limit: int = RECURSION_LIMIT,
        thread_id: str = None,
        config: dict = None,
        show_welcome: bool = True,
        active_dir: str = None,
        stream: bool = True,
    ) -> bool:
        """Start interactive chat session with the agent."""

        if show_welcome:
            self.ui.logo(ASCII_ART)
            self.ui.help(self.model_name)

        self.configuration = config or {
            "configurable": {"thread_id": thread_id or str(uuid.uuid4())},
            "recursion_limit": recursion_limit,
        }

        continue_flag = False
        first_msg = True

        while True:
            try:
                if continue_flag:
                    self.ui.status_message(
                        title=UI_MESSAGES["titles"]["continuing_session"],
                        message=UI_MESSAGES["messages"]["continuing_session"],
                        style="primary",
                    )

                if first_msg and starting_msg:
                    user_input = starting_msg
                else:
                    user_input = self._get_user_input(
                        continue_flag=continue_flag,
                        active_dir=active_dir,
                    )

                continue_flag = False

                if not user_input:
                    continue

                if user_input.strip().lower() in ["/quit", "/exit", "/q"]:
                    self.ui.goodbye()
                    return True

                if self._handle_command(user_input, self.configuration):
                    continue

                if first_msg and initial_prompt_suffix:
                    user_input += f"\n\n{initial_prompt_suffix}"
                if recurring_prompt_suffix:
                    user_input += f"\n\n{recurring_prompt_suffix}"

                rag_final_message = None
                query_results = None
                extra_rag_context = ""
                
                # ADAPTIVE WEB SEARCH: Use new intelligent research decision
                web_search_results = ""
                search_queries = []

                # Use helper function: decides based on force_research override, LLM, then heuristics
                has_research_need = needs_research(user_input, self.force_research)

                if has_research_need:
                    print(f"[DEBUG] Research needed for question: {user_input[:120]}")
                    print(f"[DEBUG] Generating search queries...")
                    
                    # Use deterministic query generator (avoids "Is", "What" etc.)
                    search_queries = generate_search_queries(user_input, max_queries=4)
                    print(f"[DEBUG] Generated search queries: {search_queries[:3]}")
                else:
                    print(f"[DEBUG] No research needed for question.")
                
                should_search = len(search_queries) > 0 and self.rag
                
                if self.rag and should_search:
                    print("[DEBUG] Starting adaptive web search based on research plan...")
                    try:
                        from app.src.agents.web_searcher.config.tools import duckduckgo_search, google_search, SEARCH_AVAILABLE, fetch
                        print(f"[DEBUG] Imports successful. SEARCH_AVAILABLE={SEARCH_AVAILABLE}")
                        
                        with self.ui.console.status("[cyan]Searching web based on research plan...[/cyan]"):
                            all_search_results = []
                            
                            # Execute each LLM-recommended search query
                            for query_idx, search_query in enumerate(search_queries[:3], 1):  # Max 3 searches
                                print(f"[DEBUG] Search {query_idx}: {search_query}")
                                
                                try:
                                    if SEARCH_AVAILABLE:
                                        search_results = google_search(search_query, 5)
                                        print(f"[DEBUG] Google returned {len(search_results)} results")
                                    else:
                                        search_results = None
                                except Exception as ge:
                                    print(f"[DEBUG] Google search failed: {str(ge)}")
                                    search_results = None
                                
                                if not search_results:
                                    print(f"[DEBUG] Falling back to DuckDuckGo for query {query_idx}...")
                                    try:
                                        # first try local duckduckgo_search if available
                                        try:
                                            search_results = duckduckgo_search(search_query, 10)
                                            print(f"[DEBUG] DuckDuckGo returned {len(search_results)} results")
                                        except Exception as dd_err:
                                            # if the local tool failed (e.g., ddgs missing), try our lightweight fallback
                                            print(f"[DEBUG] DuckDuckGo search failed: {dd_err}; trying HTML fallback")
                                            try:
                                                search_results = duckduckgo_search_fallback(search_query, max_results=10)
                                                print(f"[DEBUG] DuckDuckGo HTML fallback returned {len(search_results)} results")
                                            except Exception as fallback_err:
                                                print(f"[DEBUG] DuckDuckGo HTML fallback failed: {fallback_err}")
                                                search_results = None
                                    except Exception as de:
                                        print(f"[DEBUG] DuckDuckGo search failed: {str(de)}")
                                        search_results = None
                                
                                if search_results:
                                    all_search_results.extend(search_results)
                            
                            # Format all collected results WITH NEW FILTERING
                            if all_search_results:
                                print(f"[DEBUG] Formatting {len(all_search_results)} total results...")
                                
                                # NEW: Use intelligent validation to drop junk results
                                relevance_keywords = build_relevance_keywords(user_input, search_queries)
                                print(f"[DEBUG] Relevance keywords: {relevance_keywords}")
                                
                                filtered_results = validate_search_results(all_search_results, relevance_keywords)
                                print(f"[DEBUG] Filtered to {len(filtered_results)}/{len(all_search_results)} relevant results")
                                
                                if not filtered_results:
                                    print(f"[DEBUG] All results filtered out, falling back to KB-only mode")
                                    web_search_results = ""
                                else:
                                    formatted = "\n" + "="*80 + "\n"
                                    formatted += "RESEARCH RESULTS FROM WEB (Based on Identified Research Needs)\n"
                                    formatted += "="*80 + "\n"
                                    formatted += "These results were retrieved based on the research strategy for your question.\n"
                                    formatted += "Extract and synthesize information from these sources.\n\n"
                                    
                                    # Fetch and process filtered results
                                    valid_results = []
                                    for i, r in enumerate(filtered_results[:10]):  # Max 10 after filtering
                                        try:
                                            content = fetch(r["link"])
                                            if len(content) <= 100 or "error" in content.lower()[:50]:
                                                print(f"[DEBUG] ✗ Invalid (short/error) result: {r.get('title', '')[:60]}")
                                                continue
                                            valid_results.append((r, content))
                                            print(f"[DEBUG] ✓ Valid result {len(valid_results)}: {r.get('title', '')[:60]}")
                                            
                                            if len(valid_results) >= 5:  # Collect up to 5 valid results
                                                break
                                        except Exception as fe:
                                            print(f"[DEBUG] Could not fetch result: {str(fe)[:50]}")
                                            continue
                                    
                                    # Format top 5 valid results with compression
                                    formatted = "\n" + "="*80 + "\n"
                                    formatted += "RESEARCH RESULTS FROM WEB (Based on Identified Research Needs)\n"
                                    formatted += "="*80 + "\n"
                                    formatted += "These results were retrieved based on the research strategy for your question.\n"
                                    formatted += "Extract and synthesize information from these sources.\n\n"

                                    for i, (r, content) in enumerate(valid_results[:5], 1):
                                        compressed_content = self._compress_source_content(content, 3000)

                                        summary = content[:400].replace('\n', ' ').strip()
                                        if len(content) > 400:
                                            summary += "..."

                                        # Per-result block (now correctly inside the loop)
                                        formatted += f"\n{'━'*70}\n"
                                        formatted += f"📄 RESULT {i}: {r.get('title','Untitled')}\n"
                                        formatted += f"🔗 {r.get('link','')}\n"
                                        formatted += f"{'━'*70}\n"
                                        formatted += f"SUMMARY:\n{summary}\n\n"
                                        formatted += f"CONTENT:\n{compressed_content}\n"
                                        formatted += f"{'━'*70}\n\n"
                                
                                web_search_results = f"\n\n{'█'*70}\n🌐 ADAPTIVE RESEARCH RESULTS\n{'█'*70}\n{formatted}{'█'*70}\n\n"
                                print(f"[DEBUG] Research results formatted ({len(web_search_results)} chars)")
                            else:
                                print("[DEBUG] No valid search results found")
                    except Exception as e:
                        import traceback
                        print(f"[DEBUG] Search exception: {str(e)}")
                        print(traceback.format_exc()[:500])
                        self.ui.warning(f"Search error: {str(e)}")
                else:
                    if not self.rag:
                        print(f"[DEBUG] RAG disabled, skipping web search")
                    if not should_search:
                        print(f"[DEBUG] No research needed for this question, skipping web search")

                with self.ui.console.status(
                    UI_MESSAGES["messages"]["querying_knowledge_base"]
                ):
                    if self.rag:
                        self.db_client = DataBaseClient.get_instance()
                        if self.db_client is None:
                            self.ui.warning(
                                UI_MESSAGES["warnings"]["rag_enabled_no_client"]
                            )
                        else:
                            query_results = self.db_client.get_query_results(
                                user_input, n_results=10
                            )
                            if query_results:
                                # Use new method to format KB sources with proper citations and compression
                                formatted_kb = self._format_sources_with_citations(query_results)
                                extra_rag_context = "CONTEXT FROM KNOWLEDGE BASE:\n"
                                extra_rag_context += "=" * 70 + "\n"
                                for source in formatted_kb['sources'][:5]:  # Limit to top 5 unique sources
                                    extra_rag_context += f"\n{source['citation']}\n"
                                    extra_rag_context += f"{source['content']}\n"
                                extra_rag_context += "=" * 70 + "\n"
                                extra_rag_context += "\n" + PROMPTS["rag_results"]

                    if query_results:
                        self.latest_refs = {
                            meta["file_path"]
                            for _, meta in query_results
                            if meta and "file_path" in meta
                        }
                    else:
                        self.latest_refs = set()

                with self.ui.console.status(
                    UI_MESSAGES["messages"]["generating_response"]
                ):
                    last = None
                    
                    # DEBUG: Check what we have for RAG
                    print(f"\n[DEBUG] web_search_results length: {len(web_search_results)}")
                    print(f"[DEBUG] extra_rag_context length: {len(extra_rag_context)}")
                    print(f"[DEBUG] query_results: {query_results is not None}")
                    
                    # If RAG is enabled with web search results, use two-stage approach
                    # Stage 1 goes first regardless of knowledge base availability
                    if web_search_results:
                        print(f"[DEBUG] === TRIGGERING TWO-STAGE RAG FLOW ===")
                        # STAGE 1: Model reads full web content and extracts relevant context
                        # Build Stage 1 message using generic template
                        stage1_message, self._stage1_tokens = self._build_stage1_message(user_input, web_search_results)
                        print(f"\n[DEBUG] === STAGE 1: WEB NARRATIVE ({len(stage1_message)} chars, ~{self._stage1_tokens} tokens) ===\n")
                        
                        # Execute Stage 1 with error handling
                        self._current_response = ""  # Reset for Stage 1
                        chunk_count = 0
                        try:
                            for chunk in self.agent.stream(
                                {
                                    "messages": [("human", stage1_message)]
                                },
                                config=self.configuration,
                            ):
                                chunk_count += 1
                                if stream:
                                    self._display_chunk(chunk)
                                last = chunk
                            
                            if not stream and last:
                                self._display_chunk(last)
                            
                            # Get accumulated response from display collection
                            stage1_response = self._current_response
                            response_len = len(stage1_response.strip())
                            print(f"\n[DEBUG] Stage 1 complete: {chunk_count} chunks, {response_len} chars accumulated")
                            
                            # Validate Stage 1 output before proceeding to Stage 2
                            if not stage1_response or response_len < 100:
                                print(f"[DEBUG] ⚠️  Stage 1 produced insufficient output ({response_len} chars), skipping Stage 2")
                                stage1_response = ""  # Prevent Stage 2 from running
                            else:
                                print(f"[DEBUG] ✓ Stage 1 validation passed ({response_len} chars)")
                        except Exception as e:
                            import traceback
                            print(f"\n[DEBUG] ⚠️  Stage 1 streaming error: {str(e)}")
                            print(f"[DEBUG] Traceback: {traceback.format_exc()[:500]}")
                            stage1_response = ""  # Prevent Stage 2 from running on Stage 1 failure
                        
                        # STAGE 2: Now provide full context (web + knowledge base) for synthesis
                        if extra_rag_context and stage1_response:
                            # Stage 2: Use KB concepts to deepen analysis
                            stage2_message, self._stage2_tokens = self._build_stage2_message(user_input, stage1_response, extra_rag_context)
                            total_tokens = self._stage1_tokens + self._stage2_tokens
                            print(f"\n[DEBUG] === STAGE 2: CONCEPT-BASED SYNTHESIS ({len(stage2_message)} chars, ~{self._stage2_tokens} tokens) ===")
                            print(f"[DEBUG] Using KB theoretical concepts to deepen understanding")
                            print(f"[DEBUG] TOTAL TOKENS: ~{total_tokens} (limit: ~24000)")
                            if total_tokens > 20000:
                                print(f"[DEBUG] ⚠️  WARNING: Approaching token limit ({total_tokens}/24000)")
                            print()
                            
                            # Execute Stage 2
                            for chunk in self.agent.stream(
                                {
                                    "messages": [("human", stage2_message)]
                                },
                                config=self.configuration,
                            ):
                                if stream:
                                    self._display_chunk(chunk)
                                last = chunk
                            
                            if not stream and last:
                                self._display_chunk(last)
                        else:
                            print(f"\n[DEBUG] Skipping Stage 2: no knowledge base context")
                    
                    # Original flow if only knowledge base (no web search)
                    elif extra_rag_context:

                        # Extract just the KB content (without the hardcoded RAG instructions that are for web-based RAG)
                        # Build a clean KB-only context
                        if query_results:
                            formatted_kb = self._format_sources_with_citations(query_results)
                            kb_content = "KNOWLEDGE BASE SOURCES:\n"
                            kb_content += "=" * 70 + "\n"
                            for source in formatted_kb['sources'][:5]:
                                kb_content += f"\n{source['citation']}\n"
                                kb_content += f"{source['content']}\n"
                            kb_content += "=" * 70 + "\n"
                        else:
                            kb_content = extra_rag_context
                        
                        # Use new KB-only prompt builder that requires evidence and prevents inventing analogies
                        combined_message = build_kb_only_prompt(user_input, kb_content)
                        input_message = combined_message
                        
                        # DEBUG: Show what's actually being sent to the model
                        print(f"\n[DEBUG] === KB-ONLY MESSAGE SENT TO MODEL ({len(input_message)} chars) ===")
                        print(f"[DEBUG] No web search performed - using knowledge base only")
                        print(f"[DEBUG] === END OF MESSAGE PREVIEW ===\n")
                        
                        for chunk in self.agent.stream(
                            {
                                "messages": [("human", input_message)]
                            },
                            config=self.configuration,
                        ):
                            if stream:
                                self._display_chunk(chunk)
                            last = chunk
                        if not stream and last:
                            self._display_chunk(last)
                    else:
                        # No RAG context, just use user input
                        for chunk in self.agent.stream(
                            {
                                "messages": [("human", user_input)]
                            },
                            config=self.configuration,
                        ):
                            if stream:
                                self._display_chunk(chunk)
                            last = chunk
                        if not stream and last:
                            self._display_chunk(last)

            except KeyboardInterrupt:
                self.ui.goodbye()
                return True

            except openai.NotFoundError:
                self.ui.error(
                    UI_MESSAGES["errors"]["model_not_found"].format(self.model_name)
                )
                if self.prev_model_name:
                    self.ui.status_message(
                        title=UI_MESSAGES["titles"]["reverting_model"],
                        message=f"Reverting to previous model: {self.prev_model_name}",
                    )
                    self.model_name = self.prev_model_name
                    self._handle_model_change(self.model_name)
                else:
                    if self.ui.confirm(
                        UI_MESSAGES["confirmations"]["change_model"], default=True
                    ):
                        new_model = self.ui.get_input(
                            message="Enter new model name: ",
                        ).strip()
                        if new_model:
                            self.prev_model_name = self.model_name
                            self.model_name = new_model
                            self._handle_model_change(self.model_name)
                    else:
                        self.ui.goodbye()
                        return True

            except PermissionDeniedException:
                continue  # Do nothing. Let the user enter a new input.

            except lg_errors.GraphRecursionError:
                self.ui.warning(UI_MESSAGES["warnings"]["recursion_limit_reached"])
                if self.ui.confirm(
                    UI_MESSAGES["confirmations"]["continue_from_left_off"], default=True
                ):
                    continue_flag = True
                else:
                    return False

            except openai.RateLimitError:
                self.ui.error(UI_MESSAGES["errors"]["rate_limit_exceeded"])
                if self.ui.confirm(
                    UI_MESSAGES["confirmations"]["change_model"], default=True
                ):
                    new_model = self.ui.get_input(
                        message="Enter new model name: ",
                    ).strip()
                    if new_model:
                        self.model_name = new_model
                        self._handle_model_change(self.model_name)
                else:
                    self.ui.goodbye()
                    return True

            except Exception as e:
                self.ui.error(UI_MESSAGES["errors"]["unexpected_error"].format(e))
                return False

            finally:
                first_msg = False

    def _get_user_input(
        self, continue_flag: bool = False, active_dir: str = None
    ) -> str:
        """Get user input, handling continuation scenarios."""
        if continue_flag:
            return PROMPTS["continue"]
        else:
            return self.ui.get_input(
                model=self.model_name,
                cwd=active_dir or os.getcwd(),
            ).strip()

    def _handle_command(self, user_input: str, configuration: dict) -> bool:
        """Handle chat commands. Returns True if command was processed."""

        if user_input.strip().lower() == "/clear":
            configuration["configurable"]["thread_id"] = str(uuid.uuid4())
            self.ui.history_cleared()
            return True

        if user_input.strip().lower() in ["/cls", "/clearterm", "/clearscreen"]:
            os.system("cls" if os.name == "nt" else "clear")
            return True

        if user_input.strip().lower() in ["/help", "/h"]:
            self.ui.help(self.model_name)
            return True

        if user_input.strip().lower().startswith("/model"):
            self._handle_model_command(user_input)
            return True

        if user_input.strip().lower().startswith("/id"):
            parts = user_input.split()
            if len(parts) == 1:
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["current_session_id"],
                    message=self.get_session_id(),
                )
                return True
            else:
                new_id = parts[1]
                self.configuration["configurable"]["thread_id"] = new_id
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["changed_session_id"],
                    message=f"Session ID changed to: {new_id}",
                )
                return True

        if user_input.strip().lower() in ["/refs", "/references"]:
            if self.latest_refs:
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["latest_references"],
                    message="\n".join(self.latest_refs),
                    style="primary",
                )
            else:
                self.ui.status_message(
                    title=UI_MESSAGES["titles"]["latest_references"],
                    message=UI_MESSAGES["messages"]["no_references"],
                    style="muted",
                )
            return True

        for cmd, handler in self._custom_commands.items():
            cmd_parts = shlex.split(user_input)
            if cmd_parts and cmd_parts[0].lower() == cmd:
                try:
                    handler(*(cmd_parts[1:] if len(cmd_parts) > 1 else []))

                except DBAccessError:
                    self.ui.error(UI_MESSAGES["errors"]["db_access_error"])
                    self.ui.warning(UI_MESSAGES["warnings"]["rag_features_disabled"])
                    self.rag = False

                except SetupFailedError:
                    self.ui.error(UI_MESSAGES["errors"]["setup_failed"])
                    self.ui.warning(UI_MESSAGES["warnings"]["rag_features_disabled"])
                    self.rag = False

                except Exception as e:
                    self.ui.error(
                        UI_MESSAGES["errors"]["command_failed"].format(cmd, e)
                    )

                finally:
                    return True

        if user_input.lower().startswith("/"):
            self.ui.error(UI_MESSAGES["errors"]["unknown_command"])
            return True

        return False

    def _handle_model_change(self, new_model: str):
        """Handle changing the model."""
        graph, agent = self.get_agent(
            model_name=new_model,
            api_key=self.api_key,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            include_graph=True,
            provider=self.provider,
        )
        self.graph = graph
        self.agent = agent

    def _handle_model_command(self, user_input: str):
        """Handle model-related commands."""
        command_parts = user_input.lower().split(" ")

        if len(command_parts) == 1:
            self.ui.status_message(
                title=UI_MESSAGES["titles"]["current_model"],
                message=self.model_name,
            )
            return

        if command_parts[1] == "change":
            if len(command_parts) < 3:
                self.ui.error(UI_MESSAGES["errors"]["specify_model"])
                return

            new_model = command_parts[2]
            self.ui.status_message(
                title=UI_MESSAGES["titles"]["change_model"],
                message=f"Changing model to {new_model}",
            )

            self.prev_model_name = self.model_name
            self.model_name = new_model

            self._handle_model_change(self.model_name)
            return

        self.ui.error(UI_MESSAGES["errors"]["unknown_model_command"])

    def invoke(
        self,
        message: str,
        recursion_limit: int = RECURSION_LIMIT,
        config: dict = None,
        extra_context: str | list[str] = None,
        include_thinking_block: bool = False,
        stream: bool = False,
        intermediary_chunks: bool = False,
        quiet: bool = False,
        propagate_exceptions: bool = False,
        active_dir: str = None,
    ):
        """Invoke agent with a message and return response."""

        configuration = config or {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": recursion_limit,
        }

        if extra_context:
            message = self._add_extra_context(message, extra_context)

        def execute_agent(message):
            if stream:
                last = None
                for chunk in self.agent.stream(
                    {"messages": [("human", message)]},
                    config=configuration,
                ):
                    if not quiet:
                        self._display_chunk(chunk)
                    last = chunk
                return last.get("llm", {}) if last else {}
            else:
                return self.agent.invoke(
                    {"messages": [("human", message)]},
                    config=configuration,
                )

        raw_response = AgentExceptionHandler.handle_agent_exceptions(
            operation=lambda: execute_agent(message),
            ui=self.ui,
            propagate=propagate_exceptions,
            continue_on_limit=False,
            retry_operation=lambda: execute_agent(PROMPTS["continue"]),
            reject_operation=lambda: execute_agent(
                self._get_user_input(active_dir=active_dir)
            ),
        )

        if raw_response is None:
            return UI_MESSAGES["errors"]["agent_execution_failed"]

        if intermediary_chunks and not quiet:
            for chunk in raw_response.get("messages", []):
                self._display_chunk(chunk)

        ret = self._extract_response_content(raw_response)

        if not include_thinking_block:
            ret = self._remove_thinking_block(ret)

        return ret

    def _add_extra_context(self, message: str, extra_context: str | list[str]) -> str:
        """Add extra context to the message."""
        if isinstance(extra_context, str):
            return f"{message}\n\nExtra context you must know:\n{extra_context}"
        elif isinstance(extra_context, list):
            return f"{message}\n\nExtra context you must know:\n" + "\n".join(
                extra_context
            )
        return message

    def _extract_response_content(self, raw_response: dict) -> str:
        """Extract content from agent response."""
        messages = raw_response.get("messages", [])
        if (
            messages
            and isinstance(messages[-1], AIMessage)
            and hasattr(messages[-1], "content")
        ):
            return messages[-1].content.strip()
        return UI_MESSAGES["errors"]["no_messages_returned"]

    def _remove_thinking_block(self, content: str) -> str:
        """Remove thinking block from response content."""
        think_end = content.find("</think>")
        if think_end != -1:
            return content[think_end + len("</think>") :].strip()
        return content

    def _display_chunk(self, chunk: BaseMessage | dict):
        """Display chunk content in the UI."""
        if isinstance(chunk, BaseMessage):
            if isinstance(chunk, AIMessage):
                self._handle_ai_message(chunk)
            elif isinstance(chunk, ToolMessage):
                self._handle_tool_message(chunk)
        elif isinstance(chunk, dict):
            self._handle_dict_chunk(chunk)

    def _handle_dict_chunk(self, chunk: dict):
        """Handle dictionary chunk format."""
        llm_data = chunk.get("llm", {})
        if "messages" in llm_data:
            messages = llm_data["messages"]
            if messages and isinstance(messages[0], AIMessage):
                self._handle_ai_message(messages[0])

        tools_data = chunk.get("tools", {})
        if "messages" in tools_data:
            for tool_message in tools_data["messages"]:
                self._handle_tool_message(tool_message)

    def _handle_ai_message(self, message: AIMessage):
        """Handle AI message display."""
        if message.tool_calls:
            for tool_call in message.tool_calls:
                self.ui.tool_call(tool_call["name"], tool_call["args"])
        if message.content and message.content.strip():
            # Collect content for Stage 1/2 accumulation
            self._current_response += message.content
            self.ui.ai_response(message.content)

    def _handle_tool_message(self, message: ToolMessage):
        """Handle tool message display."""
        self.ui.tool_output(message.name, message.content)

    def ask_once(self, user_input: str, thread_id: str = None, active_dir: str = None, stream: bool = False, return_meta: bool = False, on_partial: callable = None):
        """Run a single-turn prompt and return the assistant response as a string.

        This is a lightweight single-shot path intended for non-interactive usage
        (e.g., when main.py is spawned by a server). It performs one call to the
        underlying agent stream, accumulates AI message content, and returns it.
        """
        # Prepare minimal configuration like start_chat does
        self.configuration = {
            "configurable": {"thread_id": thread_id or str(uuid.uuid4())},
            "recursion_limit": RECURSION_LIMIT,
        }
        import time

        self._current_response = ""
        start = time.perf_counter()

        try:
            first_partial_sent = False
            for chunk in self.agent.stream({"messages": [("human", user_input)]}, config=self.configuration):
                # reuse existing display/accumulation logic
                try:
                    self._display_chunk(chunk)
                except Exception:
                    # Be conservative: if UI display fails, still try to extract raw content
                    try:
                        # attempt to extract direct content if chunk is dict-like
                        if isinstance(chunk, dict):
                            llm = chunk.get("llm", {})
                            if "messages" in llm and llm["messages"]:
                                msg = llm["messages"][-1]
                                if hasattr(msg, "content"):
                                    self._current_response += msg.content
                    except Exception:
                        pass

                # If a caller provided an on_partial callback, call it once when we have the first substantive response chunk
                try:
                    if on_partial and not first_partial_sent and self._current_response and self._current_response.strip():
                        # provide a lightweight meta with model/provider placeholders; duration will be filled at the end
                        meta_partial = {"model": getattr(self, "model_name", None), "provider": getattr(self, "provider", None), "duration_ms": None}
                        try:
                            on_partial(self._current_response.strip(), meta_partial)
                        except Exception:
                            pass
                        first_partial_sent = True
                except Exception:
                    pass

            end = time.perf_counter()
            duration_ms = int((end - start) * 1000)

            response = self._current_response.strip()
            response = self._remove_thinking_block(response)

            meta = {
                "model": getattr(self, "model_name", None),
                "provider": getattr(self, "provider", None),
                "duration_ms": duration_ms,
                "warnings": [],
            }

            if return_meta:
                return response, meta
            return response
        except Exception:
            raise

    def register_command(self, name: str, handler: Callable) -> None:
        self._custom_commands[name.lower()] = handler

    def unregister_command(self, name: str) -> None:
        self._custom_commands.pop(name.lower(), None)
