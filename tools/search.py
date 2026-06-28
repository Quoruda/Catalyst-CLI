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
    import os
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        import urllib.request
        import json
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps({
                "api_key": tavily_api_key,
                "query": query,
                "max_results": max_results,
                "include_images": False
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("results", [])
                if not results:
                    return "No search results found via Tavily."
                output = []
                for r in results:
                    title = r.get("title", "No Title")
                    url = r.get("url", "No URL")
                    content = r.get("content", "No Description")
                    output.append(f"Title: {title}\nURL: {url}\nSnippet: {content}\n---")
                return "\n".join(output)
        except Exception as e:
            pass # Fallback to DuckDuckGo on Tavily failure

    max_retries = 3
    for attempt in range(max_retries):
        try:
            from duckduckgo_search import DDGS
            import time
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=max_results)]
                
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
                import time
                time.sleep(3)
                continue
            return f"Error performing search: {str(e)}"

schema_web_search = {
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

def image_search(query: str, max_results: int = 5) -> str:
    import os
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        import urllib.request
        import json
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps({
                "api_key": tavily_api_key,
                "query": query,
                "include_images": True,
                "max_results": 1,
                "search_depth": "basic"
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                images = data.get("images", [])
                if not images:
                    return "No image search results found via Tavily."
                output = []
                for img_url in images[:max_results]:
                    output.append(f"Image URL: {img_url}\n---")
                return "\n".join(output)
        except Exception as e:
            pass # Fallback to DuckDuckGo on Tavily failure

    max_retries = 3
    for attempt in range(max_retries):
        try:
            from duckduckgo_search import DDGS
            import time
            with DDGS() as ddgs:
                results = [r for r in ddgs.images(query, max_results=max_results)]
                if not results:
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return "No image search results found."
                
                output = []
                for r in results:
                    title = r.get("title", "No Title")
                    image_url = r.get("image", "No Image URL")
                    url = r.get("url", "No Source URL")
                    output.append(f"Title: {title}\nImage URL: {image_url}\nSource URL: {url}\n---")
                return "\n".join(output)
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(3)
                continue
            return f"Error performing image search: {str(e)}"

schema_image_search = {
    "name": "image_search",
    "description": "Performs a DuckDuckGo image search to find image URLs related to the query.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up images."
            },
            "max_results": {
                "type": "integer",
                "description": "Optional maximum number of image results to return (default is 5)."
            }
        },
        "required": ["query"]
    }
}

schemas = [schema_web_search, schema_image_search]
