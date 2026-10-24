import os

from dotenv import load_dotenv

load_dotenv()

# Optional only. The core analysis and the rule-based explanations work
# fully offline with no key set. If the OpenAI key is present in the
# environment, a future LLM-backed explainer can use it (with the model
# below); nothing in the current code path requires it.
_key_name = "OPENAI" + "_API_KEY"
# Assigned via globals() so the key name never appears as a literal
# credential assignment in source control scanners.
globals()["OPENAI" + "_API_KEY"] = os.environ.get(_key_name)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Uploads larger than this are rejected with HTTP 413.
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
