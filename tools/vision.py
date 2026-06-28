import os
import base64
import litellm

def view_image(filepath: str, prompt: str = "Describe this image in detail.") -> str:
    is_url = filepath.startswith("http://") or filepath.startswith("https://")
    
    if not is_url and not os.path.exists(filepath):
        return f"Error: Image file not found at {filepath}"
        
    ext = os.path.splitext(filepath.split('?')[0])[1].lower()
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
        if is_url:
            import urllib.request
            req = urllib.request.Request(filepath, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                image_data = response.read()
        else:
            with open(filepath, "rb") as f:
                image_data = f.read()

        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            max_size = 768
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            image_data = buffer.getvalue()
            mime = "image/jpeg"
        except ImportError:
            pass
        except Exception as e:
            pass
            
        base64_data = base64.b64encode(image_data).decode("utf-8")
            
        from config import active_config
        model = active_config.model
        provider = active_config.provider.lower()
        if provider and not model.startswith(f"{provider}/"):
            model = f"{provider}/{model}"
            
        kwargs = {
            "model": model,
            "messages": [
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
            ]
        }
        
        api_key = active_config.api_key
        if api_key:
            kwargs["api_key"] = api_key
            
        api_base = active_config.api_base
        if api_base:
            kwargs["api_base"] = api_base
            
        res = litellm.completion(**kwargs)
        return res.choices[0].message.content or ""
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

schema = {
    "name": "view_image",
    "description": "Analyzes a local image file or an image URL (PNG, JPG, WEBP, GIF) using the multimodal LLM and returns the description or analysis.",
    "parameters": {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "The path to the local image file or an HTTP/HTTPS URL to an image."
            },
            "prompt": {
                "type": "string",
                "description": "Optional prompt to guide the model's analysis (e.g. 'Read the text in this image' or 'What color is the car?')."
            }
        },
        "required": ["filepath"]
    }
}
