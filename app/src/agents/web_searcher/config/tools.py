from langchain_core.tools import tool
from app.src.tools.web_tools import fetch
import requests
import os


SEARCH_AVAILABLE = True


GGL_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CX_ID = os.getenv("SEARCH_ENGINE_ID")


if not GGL_API_KEY or not CX_ID:
    SEARCH_AVAILABLE = False


ENDPOINT = "https://customsearch.googleapis.com/customsearch/v1"
TIMEOUT = 10  # seconds


def duckduckgo_search(query: str, n: int = 5) -> list[dict[str, str]]:
    """Search DuckDuckGo and return structured results (fallback if Google unavailable).
    
    Args:
        query: Search query string
        n: Maximum number of results to return
        
    Returns:
        List of dictionaries with 'title' and 'link' keys
    """
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=n):
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("href", "")
                })
        return results
    except Exception as e:
        raise ValueError(f"DuckDuckGo search failed: {str(e)}")


def google_search(query: str, n: int = 5) -> list[dict[str, str]]:
    """Search Google and return structured results.

    Args:
        query: Search query string
        n: Maximum number of results to return

    Returns:
        List of dictionaries with 'title' and 'link' keys

    Raises:
        ValueError: If API key or search engine ID not configured
        requests.HTTPError: If search request fails
    """

    if not GGL_API_KEY or not CX_ID:
        raise ValueError(
            "Google API key or Search Engine ID not set in .env file. "
            "Please set GOOGLE_SEARCH_API_KEY and SEARCH_ENGINE_ID environment variables."
        )

    results, start = [], 1
    while len(results) < n:
        batch = min(10, n - len(results))
        payload = {
            "key": GGL_API_KEY,
            "cx": CX_ID,
            "q": query,
            "num": batch,
            "start": start,
        }
        resp = requests.get(ENDPOINT, params=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            results.append(
                {
                    "title": item["title"],
                    "link": item["link"],
                }
            )
            if len(results) == n:
                break

        # prepare next page (if any)
        start += batch
        if "nextPage" not in data.get("queries", {}):
            break

    return results


@tool
def search_and_scrape(query: str) -> str:
    """
    ## PRIMARY PURPOSE:
    Perform web search and extract full text content from top 5 results.

    ## WHEN TO USE:
    - Research technical topics, best practices, or implementation approaches
    - Find current information about programming languages, frameworks, tools
    - Gather multiple perspectives and comprehensive information
    - Collect up-to-date tutorials, documentation, or guides

    ## PARAMETERS:
        query (str): Search query string to find relevant web pages

    ## RETURNS:
        str: Formatted results with titles and full text content from top search results
    """
    try:
        # Try Google first if credentials available
        if SEARCH_AVAILABLE:
            try:
                search_results = google_search(query, 5)
            except Exception as e:
                # Fallback to DuckDuckGo if Google fails
                search_results = duckduckgo_search(query, 5)
        else:
            # Use DuckDuckGo if Google credentials not available
            search_results = duckduckgo_search(query, 5)
        
        if not search_results:
            return "[ERROR] No search results found."
            
        for r in search_results:
            try:
                r["full_text"] = fetch(r["link"])
            except Exception:
                r["full_text"] = "[Unable to fetch content from this link]"

        formatted_results = "Web search results:\n\n"
        for r in search_results:
            formatted_results += f"# Title: \n{r['title']}\n\n"
            formatted_results += f"# Link: {r['link']}\n\n"
            formatted_results += f"# Content: \n{r['full_text']}\n\n"

        return formatted_results
    except Exception as e:
        return f"[ERROR] Failed to perform web search: {str(e)}"
