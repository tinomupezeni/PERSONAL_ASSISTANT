"""
Deep Research Module for Ada.

Searches the web, synthesizes information, and provides executive summaries.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

BASE_DIR = Path(__file__).parent
RESEARCH_DIR = BASE_DIR / "data" / "research"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)


def web_search(query: str, max_results: int = 10) -> list[dict]:
    """
    Search the web using DuckDuckGo.

    Returns list of {title, url, snippet}
    """
    if DDGS is None:
        return [{"error": "duckduckgo-search not installed"}]

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
    except Exception as e:
        return [{"error": str(e)}]


def fetch_page_content(url: str, max_chars: int = 5000) -> str:
    """
    Fetch and extract text content from a URL.
    """
    if BeautifulSoup is None:
        return "BeautifulSoup not installed"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Get text
        text = soup.get_text(separator=" ", strip=True)

        # Clean up whitespace
        text = " ".join(text.split())

        return text[:max_chars]

    except Exception as e:
        return f"Error fetching: {e}"


def deep_research(
    topic: str,
    num_sources: int = 5,
    synthesize: bool = True
) -> dict:
    """
    Perform deep research on a topic.

    1. Search for sources
    2. Fetch content from top sources
    3. Synthesize with LLM

    Returns:
        {
            "topic": str,
            "sources": list,
            "synthesis": str,
            "timestamp": str
        }
    """
    print(f"Researching: {topic}")

    # Step 1: Search
    print("  Searching...")
    search_results = web_search(topic, max_results=num_sources + 3)

    if not search_results:
        return {
            "topic": topic,
            "error": "No search results found",
            "sources": [],
            "synthesis": ""
        }
    if isinstance(search_results[0], dict) and "error" in search_results[0]:
        return {
            "topic": topic,
            "error": search_results[0].get("error", "Search failed"),
            "sources": [],
            "synthesis": ""
        }

    # Step 2: Fetch content from top results
    print(f"  Fetching {num_sources} sources...")
    sources = []
    for result in search_results[:num_sources]:
        url = result.get("url", "")
        if not url:
            continue

        content = fetch_page_content(url, max_chars=3000)

        sources.append({
            "title": result.get("title", ""),
            "url": url,
            "snippet": result.get("snippet", ""),
            "content": content[:2000]  # Limit for LLM context
        })

    # Step 3: Synthesize with LLM
    synthesis = ""
    if synthesize and Groq and os.environ.get("GROQ_API_KEY"):
        print("  Synthesizing...")
        synthesis = synthesize_research(topic, sources)

    result = {
        "topic": topic,
        "sources": sources,
        "synthesis": synthesis,
        "timestamp": datetime.now().isoformat(),
        "num_sources": len(sources)
    }

    # Save research
    save_research(topic, result)

    return result


def synthesize_research(topic: str, sources: list[dict]) -> str:
    """
    Use LLM to synthesize research into executive summary.
    """
    client = Groq()

    # Build source context
    source_text = ""
    for i, source in enumerate(sources, 1):
        source_text += f"\n\nSOURCE {i}: {source['title']}\n"
        source_text += f"URL: {source['url']}\n"
        source_text += f"Content: {source['content'][:1500]}"

    prompt = f"""Synthesize the following research on "{topic}" into a concise executive briefing.

SOURCES:
{source_text}

REQUIREMENTS:
- Maximum 300 words
- Start with a one-sentence definition/overview
- Key facts and insights (bullet points)
- Practical applications or implications
- Note any conflicting information between sources
- Cite sources by number [1], [2], etc.

Be factual. No filler. Executive tone."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=600,
            messages=[
                {"role": "system", "content": "You are an executive research analyst. Synthesize information concisely."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Synthesis error: {e}"


def save_research(topic: str, result: dict) -> Path:
    """Save research to file."""
    # Create filename from topic
    filename = "".join(c if c.isalnum() else "_" for c in topic.lower())[:50]
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{filename}.json"

    filepath = RESEARCH_DIR / filename
    filepath.write_text(json.dumps(result, indent=2))
    return filepath


def quick_search(query: str) -> str:
    """
    Quick search - returns formatted search results without deep fetch.
    """
    results = web_search(query, max_results=5)

    if not results:
        return "Search error: No results found"
    if isinstance(results[0], dict) and "error" in results[0]:
        return f"Search error: {results[0].get('error', 'Unknown')}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['snippet'][:150]}...")
        lines.append(f"   URL: {r['url']}\n")

    return "\n".join(lines)


def get_recent_research(limit: int = 5) -> list[dict]:
    """Get recent research from history."""
    files = sorted(RESEARCH_DIR.glob("*.json"), reverse=True)[:limit]
    research = []

    for f in files:
        try:
            data = json.loads(f.read_text())
            research.append({
                "topic": data.get("topic", ""),
                "timestamp": data.get("timestamp", ""),
                "num_sources": data.get("num_sources", 0)
            })
        except:
            continue

    return research


if __name__ == "__main__":
    # Test
    print("Testing research module...")

    # Quick search
    print("\n=== Quick Search ===")
    print(quick_search("Python asyncio best practices"))

    # Deep research (uncomment to test)
    # print("\n=== Deep Research ===")
    # result = deep_research("microservices architecture patterns", num_sources=3)
    # print(result["synthesis"])
