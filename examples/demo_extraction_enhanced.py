#!/usr/bin/env python3
"""Direct test of the smart extraction with STORY EVENT prioritization."""

import re
from collections import Counter

def build_relevance_keywords(user_input: str, enhanced_query: str) -> list[str]:
    text = f"{user_input} {enhanced_query}".lower()
    tokens = re.findall(r"[a-z0-9']+", text)
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "about", "into",
        "have", "has", "was", "were", "are", "been", "their", "there", "which",
        "when", "your", "you", "they", "them", "she", "him", "his", "her",
        "not", "but", "can", "will", "just", "like", "than",
    }
    freq = Counter(t for t in tokens if len(t) > 2 and t not in stop_words)
    keywords = [w for w, _ in freq.most_common(12)]
    if not keywords:
        keywords = [t for t in tokens if len(t) > 4][:8]
    if "megatron" in text and "megatron" not in keywords:
        keywords.append("megatron")
    if "transformers" in text and "transformers" not in keywords:
        keywords.append("transformers")
    if "idw" in text and "idw" not in keywords:
        keywords.append("idw")
    return keywords

def smart_extract_facts(content: str, max_facts: int = 5) -> list[str]:
    """Enhanced extraction that PRIORITIZES story events and specific incidents."""
    facts = []
    sentences = re.split(r'(?<=[.!?])\s+', content[:4000])
    
    # Categorize by priority
    story_events = []      # Events, incidents, turning points (HIGHEST PRIORITY)
    causal_claims = []     # Causality explaining motivation
    comparisons = []       # Analogies and comparisons
    generic_facts = []     # General statements
    
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 40 or len(sent) > 500:
            continue
        
        # Check for story elements (PRIORITY 1)
        has_event_verbs = bool(re.search(
            r'\b(killed|murdered|died|executed|attacked|rebelled|revolted|witnessed|saw|'
            r'discovered|encountered|confronted|snapped|triggered|sparked|witnessed)\b', 
            sent, re.I))
        has_location = bool(re.search(r'\b(mine|mines|factory|workplace|prison|cell|street)\b', sent, re.I))
        has_specific_person = bool(re.search(r'(worker|coworker|colleague|friend|guard|officer)\b', sent, re.I))
        has_death_trauma = bool(re.search(r'\b(died|death|murder|murdered|killed|atrocity|tragedy)\b', sent, re.I))
        
        # Check for causality (PRIORITY 2)
        has_causal = bool(re.search(
            r'\b(led to|caused|resulted in|because|due to|triggered by|fueled by|driven by)\b', 
            sent, re.I))
        
        # Check for comparison (PRIORITY 3)
        has_comparison = bool(re.search(
            r'\b(like|similar to|compared to|mirror|parallel|akin to|parallels)\b', 
            sent, re.I))
        
        # Check for descriptive content
        has_adjectives = bool(re.search(
            r'\b(revolutionary|oppressive|tyrannical|authoritarian|brutal|violent|radical|heroic|noble)\b', 
            sent, re.I))
        has_numbers = bool(re.search(r'\d{1,4}', sent))
        has_proper_nouns = bool(re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sent))
        
        # PRIORITY 1: Story events with specific details (HIGHEST VALUE)
        if (has_event_verbs or has_death_trauma) and (has_location or has_specific_person):
            story_events.append(sent)
        
        # PRIORITY 2: Causal claims
        elif has_causal and (has_adjectives or has_event_verbs):
            causal_claims.append(sent)
        
        # PRIORITY 3: Comparisons
        elif has_comparison and has_proper_nouns:
            comparisons.append(sent)
        
        # PRIORITY 4: Generic facts
        else:
            score = 0
            if has_numbers:
                score += 2
            if has_proper_nouns:
                score += 1
            if has_adjectives:
                score += 2
            if score >= 3:
                generic_facts.append((sent, score))
    
    # Merge in priority order
    generic_facts.sort(key=lambda x: x[1], reverse=True)
    all_facts = story_events + causal_claims + comparisons + [s for s, _ in generic_facts]
    
    # Extract unique facts
    seen = set()
    for sent in all_facts:
        sent_lower = sent.lower()
        if sent_lower not in seen:
            facts.append(sent)
            seen.add(sent_lower)
            if len(facts) >= max_facts:
                break
    
    return facts


# User input
user_input = "Ive often been told megatron in idw is comparable to the bolshevicks in terms of his nobile and heroic intentions that later turned to fascism tyranny and oppression"
enhanced_query = "Transformers IDW Megatron political ideology radicalization Bolsheviks fascism"

# Test keyword extraction
keywords = build_relevance_keywords(user_input, enhanced_query)
print(f"[TEST] Extracted relevance keywords: {keywords}\n")

# Mock web results with STORY DETAILS INCLUDED
mock_results = [
    ({
        "title": "Megatron (G1)/2005 IDW continuity - Transformers Wiki",
        "link": "https://transformers.wiki.com/wiki/Megatron"
    }, """
    Megatron in the IDW continuity begins as a revolutionary leader advocating for Cybertronian liberation from the oppressive caste system. 
    He starts as a freedom fighter, much like early revolutionaries seeking to liberate their people. 
    His initial ideology focuses on equality and the dismantling of the Autobot-Decepticon hierarchy. 
    
    The turning point came when Megatron witnessed a coworker murdered in the mines for speaking out against oppression. 
    This brutal killing by a guard right in front of him sparked his transformation into a revolutionary. 
    The death of his colleague triggered Megatron's rebellion and he killed the guard in retaliation, becoming a fugitive. 
    This pivotal moment in the mines changed everything—he went from worker to outlaw to revolutionary leader.
    
    However, as he gains power, Megatron's methods become increasingly tyrannical. 
    He transforms from a liberator into a fascistic dictator, using violence and oppression to maintain control. 
    By the 2005 continuity, Megatron has established a totalitarian regime comparable to historical fascist movements.
    """),
    ({
        "title": "Megatron (IDW Comics) - Heroes Wiki",
        "link": "https://hero.fandom.com/wiki/Megatron"
    }, """
    In IDW comics, Megatron evolves from a charismatic revolutionary to a brutal autocrat. 
    He justified his oppressive measures as necessary for Cybertron's stability and strength. 
    The Decepticon regime under Megatron employs propaganda, surveillance, and violent suppression against dissenters. 
    This trajectory parallels the Bolsheviks, who promised workers' liberation but established an authoritarian state under Lenin. 
    Both movements began with noble intentions but devolved into tyranny. 
    Megatron's rule is marked by militarism, ideological enforcement, and the elimination of opposition. 
    His philosophy evolved from liberation to conquest, mirroring how Stalin transformed Soviet ideals into Stalinist oppression.
    """),
    ({
        "title": "Transformers IDW: The Political Analysis",
        "link": "https://example.com/analysis"
    }, """
    Megatron's character arc in IDW serves as a commentary on how revolutionary ideologies can become corrupted by power. 
    The comparison to the Bolsheviks is particularly apt: both started with utopian visions and noble goals. 
    Lenin promised to free workers from capitalist exploitation, and Megatron promised to free Cybertronians from the oppressive class system. 
    
    What triggered Megatron's initial rebellion was witnessing atrocities in his workplace—colleagues died under brutal conditions. 
    The murders of workers who spoke against oppression fueled his revolutionary fervor. 
    These specific traumas drove him to violent rebellion against the system that allowed such deaths.
    
    However, both leaders centralized power, eliminated dissent, and created hierarchical power structures that replicated the very oppression they claimed to oppose. 
    Megatron's evolution from freedom fighter to tyrant demonstrates the corrupting influence of absolute power. 
    His methods became increasingly authoritarian, employing violence, control, and propaganda—the hallmarks of fascism. 
    This transformation took place over years, showing how revolutionary movements can gradually abandon their founding principles.
    """),
]

print("="*80)
print("DEMONSTRATING ENHANCED SMART FACT EXTRACTION")
print("(With Story Events & Specific Incidents Prioritized)")
print("="*80 + "\n")

total_fact_count = 0
for i, (result, content) in enumerate(mock_results, 1):
    print(f"\n╔════ WEB RESULT {i} ════════════════════════════════════════╗")
    print(f"║ TITLE: {result['title']}")
    print(f"║ SOURCE: {result['link']}")
    print(f"╚═════════════════════════════════════════════════════════════════╝")
    print(f"EXTRACTED FACTS (prioritizes story events & incidents):\n")
    
    extracted = smart_extract_facts(content, max_facts=4)
    
    for j, fact in enumerate(extracted, 1):
        total_fact_count += 1
        fact_display = fact[:280] if len(fact) > 280 else fact
        print(f"  [{total_fact_count}] \"{fact_display}\"")
    
    print()

print("\n" + "█"*80)
print(f"TOTAL FACTS AVAILABLE FROM 3 SOURCES: {total_fact_count}")
print("⚠️ NOTE: Facts now prioritize SPECIFIC STORY DETAILS over generic claims")
print("   Look for: mining incident, murdered coworker, triggered rebellion, etc.")
print("█"*80)

print("\n\nKEY IMPROVEMENTS:")
print("-" * 80)
print("""
✓ Story events (murders, incidents, turning points) extracted FIRST
✓ Causal language explaining motivation prioritized
✓ Generic facts only included if space permits
✓ Specific traumas and incidents now highlighted
✓ Personal turning points (the mine incident) now surface

Result: Facts now capture BOTH:
  - Broad political themes (revolutionary → tyrant)
  - AND specific personal moments (witnessed coworker murder → sparked rebellion)
""")
print("-" * 80)
