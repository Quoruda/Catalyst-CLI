import trafilatura

def read_webpage(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return f"Error: Unable to fetch URL content for {url}."
        content = trafilatura.extract(downloaded, output_format="markdown", include_images=True)
        return content or "Error: No main text or content could be extracted from this webpage."
    except Exception as e:
        return f"Error reading webpage: {str(e)}"

schema = {
    "name": "read_webpage",
    "description": "Fetches a webpage from a URL and extracts its main text content in clean markdown format.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the webpage to read."
            }
        },
        "required": ["url"]
    }
}
