import os
import base64
import litellm

def view_image(filepath: str, prompt: str = "Describe this image in detail.") -> str:
    if not os.path.exists(filepath):
        return f"Error: Image file not found at {filepath}"
        
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".png", ".apng"):
        mime = "image/png"
    elif ext in (".jpg", ".jpeg", ".jpe"):
        mime = "image/jpeg"
    elif ext in (".webp",):
        mime = "image/webp"
    elif ext in (".gif",):
        mime = "image/gif"
    else:
        mime = "image/jpeg"
        
    try:
        with open(filepath, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
            
        model = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if provider == "gemini" and not model.startswith("gemini/"):
            model = f"gemini/{model}"
            
        res = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{base64_data}"
                            }
                        }
                    ]
                }
            ],
            api_key=os.getenv("LLM_API_KEY")
        )
        return res.choices[0].message.content or ""
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

schema = {
    "name": "view_image",
    "description": "Analyzes a local image file (PNG, JPG, WEBP, GIF) using the multimodal LLM and returns the description or analysis.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The path to the local image file."
            },
            "prompt": {
                "type": "string",
                "description": "Optional prompt to guide the model's analysis (e.g. 'Read the text in this image' or 'What color is the car?')."
            }
        },
        "required": ["filepath"]
    }
}
