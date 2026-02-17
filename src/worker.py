import json
import os
import time
import urllib.error
import urllib.request

from storage import init_db, open_connection, utc_now

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
POLL_INTERVAL = float(os.getenv("OLLAMA_POLL_INTERVAL", "1.0"))


def claim_prompt():
    with open_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, prompt FROM prompts WHERE status = 'queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            conn.execute("COMMIT")
            return None
        now = utc_now()
        cursor = conn.execute(
            "UPDATE prompts SET status = 'processing', updated_at = ? WHERE id = ? AND status = 'queued'",
            (now, row["id"]),
        )
        if cursor.rowcount == 0:
            conn.execute("COMMIT")
            return None
        conn.execute("COMMIT")
        return {"id": row["id"], "prompt": row["prompt"]}


def call_ollama(prompt_text: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt_text,
        "stream": False,
        "options": {"num_keep": 0},
        "keep_alive": 0
    }).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("response", "")


def complete_prompt(prompt_id: str, result: str) -> None:
    now = utc_now()
    with open_connection() as conn:
        conn.execute(
            "UPDATE prompts SET status = 'completed', result = ?, updated_at = ? WHERE id = ?",
            (result, now, prompt_id),
        )
        conn.commit()


def run_worker() -> None:
    init_db()
    print(f"Worker polling {OLLAMA_URL} using model {MODEL}")
    while True:
        item = claim_prompt()
        if item is None:
            time.sleep(POLL_INTERVAL)
            continue
        try:
            result = call_ollama(item["prompt"])
        except urllib.error.URLError as exc:
            result = f"Worker error: {exc}"
        complete_prompt(item["id"], result)


if __name__ == "__main__":
    run_worker()
