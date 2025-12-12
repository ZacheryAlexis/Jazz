#!/usr/bin/env python3
"""Direct test of the smart extraction and fact citation blocks."""

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
    facts = []
    sentences = re.split(r'(?<=[.!?])\s+', content[:4000])
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 40 or len(sent) > 500:
            continue
        has_numbers = bool(re.search(r'\d{1,4}', sent))
        has_proper_nouns = bool(re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sent))
        has_causal = bool(re.search(r'\b(led to|caused|resulted in|because|due to|through|via|by)\b', sent, re.I))
        has_comparison = bool(re.search(r'\b(like|similar to|compared to|as|mirror|parallel|akin to)\b', sent, re.I))
        has_adjectives = bool(re.search(r'\b(revolutionary|oppressive|tyrannical|authoritarian|brutal|violent|powerful|radical|heroic|noble)\b', sent, re.I))
        score = 0
        if has_numbers:
            score += 2
        if has_proper_nouns:
            score += 1
        if has_causal or has_comparison:
            score += 3
        if has_adjectives:
            score += 2
        if score >= 3:
            facts.append(sent)
            if len(facts) >= max_facts:
                break
    if len(facts) < 2:
        for sent in sentences[:6]:
            sent = sent.strip()
            if len(sent) > 40 and len(sent) < 500 and sent not in facts:
                facts.append(sent)
                if len(facts) >= max_facts:
                    break
    return facts

# Test user input
user_input = "Ive often been told megatron in idw is comparable to the bolshevicks in terms of his nobile and heroic intentions that later turned to fascism tyranny and oppression"
enhanced_query = "Transformers IDW Megatron political ideology radicalization Bolsheviks fascism"

# Test keyword extraction
keywords = build_relevance_keywords(user_input, enhanced_query)
print(f"[TEST] Extracted relevance keywords: {keywords}\n")

# Mock web results with realistic IDW content
mock_results = [
    ({
        "title": "Megatron (G1)/2005 IDW continuity - Transformers Wiki",
        "link": "https://transformers.wiki.com/wiki/Megatron"
    }, """
    Megatron in the IDW continuity begins as a revolutionary leader advocating for Cybertronian liberation from the oppressive caste system. He starts as a freedom fighter, much like early revolutionaries seeking to liberate their people. His initial ideology focuses on equality and the dismantling of the Autobot-Decepticon hierarchy. However, as he gains power, Megatron's methods become increasingly tyrannical. He transforms from a liberator into a fascistic dictator, using violence and oppression to maintain control. By the 2005 continuity, Megatron has established a totalitarian regime comparable to historical fascist movements. His transformation mirrors how revolutionaries often become oppressors once they achieve power.
    """),
    ({
        "title": "Megatron (IDW Comics) - Heroes Wiki",
        "link": "https://hero.fandom.com/wiki/Megatron"
    }, """
    In IDW comics, Megatron evolves from a charismatic revolutionary to a brutal autocrat. He justified his oppressive measures as necessary for Cybertron's stability and strength. The Decepticon regime under Megatron employs propaganda, surveillance, and violent suppression against dissenters. This trajectory parallels the Bolsheviks, who promised workers' liberation but established an authoritarian state under Lenin. Both movements began with noble intentions but devolved into tyranny. Megatron's rule is marked by militarism, ideological enforcement, and the elimination of opposition. His philosophy evolved from liberation to conquest, mirroring how Stalin transformed Soviet ideals into Stalinist oppression.
    """),
    ({
        "title": "Transformers IDW: The Political Analysis",
        "link": "https://example.com/analysis"
    }, """
    Megatron's character arc in IDW serves as a commentary on how revolutionary ideologies can become corrupted by power. The comparison to the Bolsheviks is particularly apt: both started with utopian visions and noble goals. Lenin promised to free workers from capitalist exploitation, and Megatron promised to free Cybertronians from the oppressive class system. However, both leaders centralized power, eliminated dissent, and created hierarchical power structures that replicated the very oppression they claimed to oppose. Megatron's evolution from freedom fighter to tyrant demonstrates the corrupting influence of absolute power. His methods became increasingly authoritarian, employing violence, control, and propaganda—the hallmarks of fascism. This transformation took place over years, showing how revolutionary movements can gradually abandon their founding principles.
    """),
]

print("="*80)
print("DEMONSTRATING SMART FACT EXTRACTION")
print("="*80 + "\n")

total_fact_count = 0
for i, (result, content) in enumerate(mock_results, 1):
    print(f"\n╔════ WEB RESULT {i} ════════════════════════════════════════╗")
    print(f"║ TITLE: {result['title']}")
    print(f"║ SOURCE: {result['link']}")
    print(f"╚═════════════════════════════════════════════════════════════════╝")
    print(f"EXTRACTED FACTS (cite these verbatim):\n")
    
    extracted = smart_extract_facts(content, max_facts=4)
    
    for j, fact in enumerate(extracted, 1):
        total_fact_count += 1
        fact_display = fact[:280] if len(fact) > 280 else fact
        print(f"  [{total_fact_count}] \"{fact_display}\"")
    
    print()

print("\n" + "█"*80)
print(f"TOTAL FACTS AVAILABLE FROM 3 SOURCES: {total_fact_count}")
print("⚠️ MODEL SHOULD CITE AT LEAST 8 OF THESE IN SECTION 1")
print("█"*80)

print("\n\nEXPECTED SECTION 1 FORMAT:")
print("-" * 80)
print("""
SECTION 1: WEB RESEARCH FACTS

1. Web Result 1: "Megatron in the IDW continuity begins as a revolutionary leader advocating for Cybertronian liberation from the oppressive caste system."

2. Web Result 1: "His initial ideology focuses on equality and the dismantling of the Autobot-Decepticon hierarchy."

3. Web Result 1: "However, as he gains power, Megatron's methods become increasingly tyrannical."

4. Web Result 1: "He transforms from a liberator into a fascistic dictator, using violence and oppression to maintain control."

5. Web Result 2: "In IDW comics, Megatron evolves from a charismatic revolutionary to a brutal autocrat."

6. Web Result 2: "This trajectory parallels the Bolsheviks, who promised workers' liberation but established an authoritarian state under Lenin."

7. Web Result 3: "The comparison to the Bolsheviks is particularly apt: both started with utopian visions and noble goals."

8. Web Result 3: "Megatron's evolution from freedom fighter to tyrant demonstrates the corrupting influence of absolute power."

[Additional facts from Section 1 implementation would continue...]
""")
print("-" * 80)
