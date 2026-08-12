from typing import List, Dict
from app.config import settings

# Load tag-to-system-prompt mapping once at startup from the configured file path
try:
    SYSTEM_PROMPTS = settings.load_system_prompts()
except Exception as e:
    # Fallback to an empty dict; config validation will handle fallback creation dynamically
    SYSTEM_PROMPTS = {}

async def build_chunk_payload(
    tag: str,
    image_b64_list: List[str],
    start_page: int,
    total_pages: int,
    model_name: str,
    max_tokens: int,
    temperature: float
) -> Dict:
    """
    Builds the OpenAI-compatible completions JSON payload for a chunk of pages.
    Each page image is appended as an image_url content block using JPEG data URIs.
    """
    system_prompt = SYSTEM_PROMPTS.get(tag)
    if not system_prompt:
        system_prompt = (
            f"You are an expert document OCR engine. Perform OCR on this {tag} document. "
            "Extract all text, tables, and structures and represent them in structured markdown."
        )

    end_page = start_page + len(image_b64_list) - 1

    # Detailed, precise OCR instruction for the chunk of pages
    user_content = [
        {
            "type": "text",
            "text": (
                f"Please transcribe and perform high-quality OCR on pages {start_page} through {end_page} (out of {total_pages} pages total) "
                f"of this {tag} document. Output the combined transcribed content in structured markdown format. "
                "Ensure that table formatting, headers, list items, and values are fully preserved in sequence. "
                "Do not add any conversational introduction, explanation, or notes. Output ONLY the extracted markdown."
            )
        }
    ]

    # Append each page image as an image_url content block using JPEG format data URIs
    for img_b64 in image_b64_list:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_b64}"
            }
        })

    # Construct messages list, omitting the system prompt for chandra and docling models
    messages = []
    if system_prompt and "chandra" not in model_name.lower() and "docling" not in model_name.lower():
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
    messages.append({
        "role": "user",
        "content": user_content
    })

    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    return payload
