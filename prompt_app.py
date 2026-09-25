import json
import logging
import uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field

from check_prompt_pin import ROOT, validate

CONFIG, PIN = validate()
PROMPT = json.loads((ROOT / "prompts" / PIN["file"]).read_text())
app = FastAPI(title="AfyaPlus release simulation", version=CONFIG["app_version"])
log = logging.getLogger("uvicorn.error")


def predict(message, prompt=PROMPT):
    terms = prompt["high_urgency_terms"]
    if not isinstance(terms, list) or not terms or any(not isinstance(t, str) or not t for t in terms):
        raise ValueError("Invalid prompt rules")
    return "high" if any(term in message.lower() for term in terms) else "low"


class Request(BaseModel):
    patient_message: str = Field(min_length=5, max_length=1000)


@app.get("/health")
def health():
    return {"service": "afyaplus-triage", **CONFIG, "prompt_sha": PIN["sha256"]}


@app.post("/triage")
def triage(body: Request):
    trace_id = str(uuid.uuid4())
    log.info(json.dumps({"event": "triage", "trace_id": trace_id,
                         "prompt_version": PIN["version"]}))
    return {"urgency": predict(body.patient_message), "trace_id": trace_id,
            "provider": CONFIG["provider"], "simulation": True}
