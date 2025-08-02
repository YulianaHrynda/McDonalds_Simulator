import os
import json
from pathlib import Path
from openai import OpenAI
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def load_prompt(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()

PROMPT_PATH = Path("core/prompts/order_parser.txt")
SYSTEM_PROMPT = load_prompt(PROMPT_PATH)

def parse_order(user_message: str) -> Dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.2
    )

    raw = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw)
        for item in parsed.get("items", []):
            item.setdefault("quantity", 1)
        return parsed
    except Exception as e:
        return {"intent": "clarify", "raw": raw, "error": str(e)}
