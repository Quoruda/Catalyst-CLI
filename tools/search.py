import warnings

original_warn = warnings.warn
def custom_warn(message, category=None, stacklevel=1, source=None):
    if "duckduckgo_search" in str(message) or "renamed to `ddgs`" in str(message):
        return
    original_warn(message, category, stacklevel, source)
warnings.warn = custom_warn

from duckduckgo_search import DDGS

import time

def web_search(query: str, max_results: int = 5) -> str:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=max_results)]
                
                # Si DuckDuckGo nous bloque silencieusement (renvoie une liste vide), on retente
                if not results:
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return "No search results found."
                
                output = []
                for r in results:
                    title = r.get("title", "No Title")
                    url = r.get("href", "No URL")
                    body = r.get("body", "No Description")
                    output.append(f"Title: {title}\nURL: {url}\nSnippet: {body}\n---")
                return "\n".join(output)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return f"Error performing search: {str(e)}"

schema = {
    "name": "web_search",
    "description": "Performs a DuckDuckGo web search to find websites and information related to the query.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up on the web."
            },
            "max_results": {
                "type": "integer",
                "description": "Optional maximum number of search results to return (default is 5)."
            }
        },
        "required": ["query"]
    }
}
