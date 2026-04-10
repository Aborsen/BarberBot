import base64
import asyncio
import json
import re
from openai import AsyncOpenAI
from config import (
    XAI_API_KEY,
    XAI_BASE_URL,
    OPENAI_API_KEY,
    VISION_MODEL,
    IMAGE_MODEL,
    NUM_HAIRSTYLES,
)

# xAI client for vision analysis
client = AsyncOpenAI(api_key=XAI_API_KEY, base_url=XAI_BASE_URL)

# OpenAI client for image generation
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are an expert barber and hairstylist assistant. "
    "Your job is to look at hair in photos and suggest suitable haircut options. "
    "You only analyze hair characteristics — type, texture, length, and style — "
    "and suggest appropriate cuts. You never identify or describe people."
)

USER_PROMPT = """Look at the hair in this image and describe what you see, then suggest 6 haircut options.

Analyze only the hair:
- Hair type: straight / wavy / curly / coily
- Hair texture: fine / medium / thick
- Current length: very short / short / medium / long / very long
- Current style: how is it currently worn

Then suggest 6 distinct haircut options that would work well for this hair type.

For each option provide:
- name: haircut name
- reason: one sentence why it suits this hair type
- image_prompt: a detailed DALL-E style prompt to generate a photorealistic image of a man with this exact haircut. Describe the haircut in detail (length on top, sides, back, texture, styling). Start each prompt with "Photorealistic portrait photo of a man with"

Respond with ONLY a valid JSON object, no markdown, no explanation:
{
  "hair_type": "...",
  "hair_texture": "...",
  "hair_length": "...",
  "current_style": "...",
  "hairstyles": [
    {
      "name": "...",
      "reason": "...",
      "image_prompt": "..."
    }
  ]
}"""


async def analyze_photo_and_get_hairstyles(photo_bytes: bytes) -> dict:
    """
    Analyzes the user's photo using Grok Vision and returns hairstyle recommendations.
    """
    base64_image = base64.b64encode(photo_bytes).decode("utf-8")

    response = await client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                    {
                        "type": "text",
                        "text": USER_PROMPT,
                    },
                ],
            },
        ],
        max_tokens=2000,
    )

    message = response.choices[0].message

    if message.content is None:
        refusal = getattr(message, "refusal", None)
        raise ValueError(f"Grok refused the request: {refusal}")

    content = message.content.strip()
    print(f"[Vision] finish_reason={response.choices[0].finish_reason!r}")
    print(f"[Vision] content={content[:200]!r}...")

    if not content or content.startswith("I'm sorry") or content.startswith("I cannot"):
        print(f"[Vision] Soft refusal: {content!r}")
        return {}

    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", content)
    if match:
        content = match.group(1)

    # Find JSON object in the response
    json_match = re.search(r"\{[\s\S]*\}", content)
    if json_match:
        content = json_match.group(0)

    result = json.loads(content)
    return result


def _build_edit_prompt(hairstyle: dict) -> str:
    """
    Builds a prompt for Grok image generation to show a hairstyle.
    Uses the detailed image_prompt from the analysis.
    """
    return hairstyle.get("image_prompt", f"Photorealistic portrait photo of a man with a {hairstyle.get('name', 'hairstyle')}")


async def generate_hairstyle_image(prompt: str, original_photo: bytes) -> bytes:
    """
    Generates a hairstyle image using OpenAI image editing.
    Edits the user's actual photo to apply the hairstyle, preserving likeness.
    Returns image bytes.
    """
    response = await openai_client.images.edit(
        model=IMAGE_MODEL,
        image=("photo.jpg", original_photo, "image/jpeg"),
        prompt=prompt,
        n=1,
        size="1024x1024",
    )

    image_b64 = response.data[0].b64_json
    return base64.b64decode(image_b64)


async def generate_all_hairstyle_images(
    analysis: dict, original_photo: bytes
) -> list[dict]:
    """
    Generates all 6 hairstyle images concurrently.
    Returns a list of dicts with 'name', 'reason', and 'image_bytes'.
    """
    hairstyles = analysis.get("hairstyles", [])[:NUM_HAIRSTYLES]

    async def generate_one(hairstyle: dict) -> dict:
        prompt = _build_edit_prompt(hairstyle)
        print(f"[Image Gen] Generating: {hairstyle.get('name')}")
        print(f"[Image Gen] Prompt: {prompt[:100]}...")
        image_bytes = await generate_hairstyle_image(prompt, original_photo)
        return {
            "name": hairstyle.get("name", "Hairstyle"),
            "reason": hairstyle.get("reason", ""),
            "image_bytes": image_bytes,
        }

    tasks = [generate_one(h) for h in hairstyles]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = []
    for r in results:
        if isinstance(r, Exception):
            print(f"[Image Gen] Failed: {r}")
        else:
            successful.append(r)

    return successful
