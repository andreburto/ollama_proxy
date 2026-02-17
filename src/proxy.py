import json
import os
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from storage import init_db, open_connection, utc_now

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
HOST = "0.0.0.0"
PORT = 8000


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    body = handler.rfile.read(length)
    return json.loads(body.decode("utf-8"))


def write_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(data)


class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/api/v1/prompt":
            self.handle_prompt_submit()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.serve_index()
            return
        if parsed.path.startswith("/api/v1/prompt/"):
            self.handle_prompt_query(parsed.path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def serve_index(self) -> None:
        index_path = os.path.join(STATIC_DIR, "index.html")
        if not os.path.exists(index_path):
            self.send_error(HTTPStatus.NOT_FOUND, "Frontend not found")
            return
        with open(index_path, "rb") as handle:
            data = handle.read()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def handle_prompt_submit(self) -> None:
        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            write_json(self, HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON"})
            return
        prompt = (payload.get("prompt") or "").strip()
        if not prompt:
            write_json(self, HTTPStatus.BAD_REQUEST, {"error": "Prompt is required"})
            return
        prompt_id = str(uuid.uuid4())
        now = utc_now()
        with open_connection() as conn:
            conn.execute(
                "INSERT INTO prompts (id, prompt, status, result, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (prompt_id, prompt, "queued", None, now, now),
            )
            conn.commit()
        write_json(self, HTTPStatus.OK, {"id": prompt_id})

    def handle_prompt_query(self, path: str) -> None:
        parts = path.strip("/").split("/")
        if len(parts) != 5:
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        _, _, _, prompt_id, action = parts
        if action == "status":
            self.send_prompt_status(prompt_id)
            return
        if action == "result":
            self.send_prompt_result(prompt_id)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def send_prompt_status(self, prompt_id: str) -> None:
        with open_connection() as conn:
            row = conn.execute(
                "SELECT id, status FROM prompts WHERE id = ?",
                (prompt_id,),
            ).fetchone()
        if row is None:
            write_json(self, HTTPStatus.NOT_FOUND, {"error": "Prompt not found"})
            return
        write_json(self, HTTPStatus.OK, {"id": row["id"], "status": row["status"]})

    def send_prompt_result(self, prompt_id: str) -> None:
        with open_connection() as conn:
            row = conn.execute(
                "SELECT id, status, result FROM prompts WHERE id = ?",
                (prompt_id,),
            ).fetchone()
        if row is None:
            write_json(self, HTTPStatus.NOT_FOUND, {"error": "Prompt not found"})
            return
        if row["status"] != "completed":
            write_json(
                self,
                HTTPStatus.ACCEPTED,
                {"id": row["id"], "status": row["status"]},
            )
            return
        write_json(
            self,
            HTTPStatus.OK,
            {"id": row["id"], "status": row["status"], "result": row["result"]},
        )

    def log_message(self, format: str, *args) -> None:
        if os.getenv("OLLAMA_PROXY_QUIET"):
            return
        super().log_message(format, *args)


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), ProxyHandler)
    print(f"Ollama proxy listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
