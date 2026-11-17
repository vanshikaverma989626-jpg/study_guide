import json
import os
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

# In-memory API key storage for current session
_RUNTIME_API_KEY: Optional[str] = None

# Active candidate models in order of priority (handles deprecation, quota & capacity spikes)
CANDIDATE_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemma-4-26b-a4b-it",
    "gemini-flash-latest",
    "gemini-3.8-flash"
]


def set_api_key(key: str, save_to_file: bool = True) -> bool:
    global _RUNTIME_API_KEY
    clean_key = key.strip()
    if not clean_key:
        return False

    _RUNTIME_API_KEY = clean_key

    if save_to_file:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            key_file = os.path.join(base_dir, "api_key.txt")
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(clean_key)
            return True
        except Exception as e:
            print(f"[Warning] Could not save API key to file: {e}")
    return True


def get_api_key() -> Optional[str]:
    global _RUNTIME_API_KEY
    if _RUNTIME_API_KEY:
        return _RUNTIME_API_KEY

    # Check environment variable
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    # Check api_key.txt or .env file in project directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in ["api_key.txt", ".env"]:
        fpath = os.path.join(base_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
                        elif line and not line.startswith("#") and len(line) > 20:
                            return line
            except Exception:
                pass

    return None


def is_ai_available() -> bool:
    return get_api_key() is not None


def call_gemini_api(prompt: str, temperature: float = 0.3) -> Optional[str]:
    api_key = get_api_key()
    if not api_key:
        return None
    # Try each candidate model until one succeeds
    for model_name in CANDIDATE_MODELS:
        # Method 1: Try using the google-generativeai SDK if installed
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except ImportError:
            pass
        except Exception:
            pass

        # Method 2: Direct REST request with standard Python urllib
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 2048
                }
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=18) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
        except urllib.error.HTTPError as http_err:
            # If 404 (model deprecated), 429 (rate/quota exceeded on this model), or 503 (high demand), try next model!
            if http_err.code in {404, 429, 503}:
                continue
            elif http_err.code in {400, 403}:
                print(f"\n[AI Error] Gemini API returned HTTP {http_err.code}. Check that your API key is valid.")
                return None
        except Exception:
            continue

    print("\n[AI Error] All Gemini model endpoints failed. Falling back to offline mode.")
    return None


def extract_json_from_response(raw_text: str) -> Optional[Any]:
    if not raw_text:
        return None
    cleaned = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        cleaned = match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Search for first { and last }
        start_brace = cleaned.find("{")
        end_brace = cleaned.rfind("}")
        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            try:
                return json.loads(cleaned[start_brace:end_brace+1])
            except Exception:
                pass
        # Search for first [ and last ]
        start_bracket = cleaned.find("[")
        end_bracket = cleaned.rfind("]")
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            try:
                return json.loads(cleaned[start_bracket:end_bracket+1])
            except Exception:
                pass
    return None


def find_stages_list(data: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return data
        return None
    if isinstance(data, dict):
        # 1. Check common roadmap keys
        for key in ["stages", "roadmap", "learning_path", "curriculum", "steps", "modules", "path"]:
            if key in data:
                val = data[key]
                if isinstance(val, list) and val and isinstance(val[0], dict):
                    return val
                if isinstance(val, dict):
                    nested = find_stages_list(val)
                    if nested:
                        return nested

        # 2. Search any key that holds a list of dicts with stage-like attributes
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                first_item = v[0]
                stage_indicators = {"stage", "stage_number", "title", "name", "level", "topics", "subtopics", "description", "key_activities"}
                if any(ind in first_item for ind in stage_indicators):
                    return v
            elif isinstance(v, dict):
                nested = find_stages_list(v)
                if nested:
                    return nested
    return None

def find_resources_list(data: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return data
        return None
    if isinstance(data, dict):
        for key in ["resources", "learning_resources", "materials", "links", "recommendations"]:
            if key in data:
                val = data[key]
                if isinstance(val, list) and val and isinstance(val[0], dict):
                    return val
                if isinstance(val, dict):
                    nested = find_resources_list(val)
                    if nested:
                        return nested

        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
            elif isinstance(v, dict):
                nested = find_resources_list(v)
                if nested:
                    return nested
    return None

# LLM FEATURE 1: Ask AI Tutor (Doubt Solver & Concept Explainer)
def ask_ai_tutor(question: str) -> Optional[str]:
    prompt = f"""You are a friendly, patient computer science tutor helping an undergraduate student.
Answer this student question clearly, simply, and engagingly.

Student Question:
"{question}"

Please format your response in clean Markdown with:
1. Simple Core Concept (explained in 2-3 plain sentences)
2. Real-World Analogy (to make it intuitive and memorable)
3. Concrete Example / Code Snippet (short and beginner friendly)
4. Quick Exam / Viva Tip
"""
    return call_gemini_api(prompt, temperature=0.4)

# LLM FEATURE 2: Generative Note Summarization
def generate_notes_summary_ai(notes_text: str, length: str = "medium") -> Optional[str]:
    num_points = {"short": "3 concise", "medium": "5 clear", "detailed": "7-8 thorough"}.get(length.lower(), "5 clear")

    prompt = f"""You are an expert academic study assistant.
Read the student notes below and generate a {num_points} bullet-point summary.
Highlight critical technical keywords using markdown bold (e.g. **keyword**).

Student Notes:
\"\"\"
{notes_text}
\"\"\"

Output format:
### Notes Summary ({length.capitalize()} Length)
- Bullet point 1
- Bullet point 2
...
"""
    return call_gemini_api(prompt, temperature=0.2)

# LLM FEATURE 3: Dynamic Roadmap, Resources & Summary for ANY Topic
def generate_roadmap_ai(topic: str) -> Optional[List[Dict[str, Any]]]:
    prompt = f"""You are an expert curriculum designer.
Create a structured 6-stage learning roadmap for the topic: "{topic}".
Output ONLY valid JSON (no markdown formatting outside JSON) matching this exact schema:
{{
  "stages": [
    {{
      "stage_number": 1,
      "level": "Beginner",
      "title": "Stage Title",
      "time_estimate": "1–2 weeks",
      "subtopics": ["Subtopic 1", "Subtopic 2", "Subtopic 3"],
      "practice_task": "A concrete mini project or practice task"
    }}
  ]
}}
Provide 6 ordered stages spanning Beginner (stages 1-2), Intermediate (stages 3-4), and Advanced (stages 5-6).
"""
    raw_response = call_gemini_api(prompt, temperature=0.3)
    if not raw_response:
        return None

    data = extract_json_from_response(raw_response)
    stages = find_stages_list(data)
    return stages


def generate_resources_ai(topic: str) -> Optional[List[Dict[str, Any]]]:
    prompt = f"""You are an educational advisor.
Provide 5-6 high quality learning resources for the topic: "{topic}".
Group them across these types: Free courses, YouTube channels, Books, Practice websites, Documentation.

Output ONLY valid JSON matching this schema:
{{
  "resources": [
    {{
      "type": "Documentation",
      "name": "Resource Name",
      "reason": "One line explanation of why this resource is useful.",
      "url": "https://official-or-wellknown-domain.com/"
    }}
  ]
}}
IMPORTANT: Do not invent URLs. Use only real official sites or leave url empty.
"""
    raw_response = call_gemini_api(prompt, temperature=0.3)
    if not raw_response:
        return None

    data = extract_json_from_response(raw_response)
    return find_resources_list(data)


def generate_summary_ai(topic: str) -> Optional[Dict[str, Any]]:
    prompt = f"""You are an academic computer science professor.
Provide a clear structured summary of the topic: "{topic}".

Output ONLY valid JSON with this schema:
{{
  "definition": "Clear 1-2 sentence definition.",
  "key_concepts": [
    "Concept 1: Short explanation",
    "Concept 2: Short explanation",
    "Concept 3: Short explanation",
    "Concept 4: Short explanation"
  ],
  "real_world_uses": [
    "Real world application 1",
    "Real world application 2",
    "Real world application 3"
  ],
  "common_mistakes": [
    "Common mistake 1 and how to avoid it",
    "Common mistake 2 and how to avoid it"
  ]
}}
"""
    raw_response = call_gemini_api(prompt, temperature=0.3)
    if not raw_response:
        return None
    return extract_json_from_response(raw_response)
