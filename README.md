# Ollama Proxy

A queue-based proxy server for the Ollama API that handles slow response times by implementing a queuing system with status tracking and result retrieval.

## Description

Ollama Proxy is designed to facilitate communication between clients and the Ollama API by implementing an asynchronous queuing system. Instead of waiting for synchronous responses from the potentially slow Ollama API, clients submit prompts and receive a unique ID immediately. They can then poll for status updates and retrieve results when processing is complete.

The project consists of three main components:
- **Proxy Server**: HTTP server that accepts prompts, manages the queue, and serves the frontend
- **Worker**: Background process that continuously processes queued prompts using the Ollama API
- **Frontend**: Simple web interface for submitting prompts and viewing results

Key features:
- Asynchronous prompt processing with queue management
- RESTful API for status tracking and result retrieval
- SQLite-based persistence for prompts and results
- CORS-enabled for cross-origin requests
- Single-file frontend with no external dependencies
- Configurable via environment variables

## Files

### Core Components

- **src/proxy.py**: HTTP server that handles API endpoints and serves the frontend. Manages prompt submission, status checks, and result retrieval. Uses Python's `http.server` module with threading support for concurrent requests.

- **src/worker.py**: Background worker that continuously polls the queue for new prompts, processes them using the Ollama API (model: `llama3.2`), and updates their status and results in the database. Runs independently from the proxy server.

- **src/storage.py**: Database management module that provides connection handling, schema initialization, and utility functions for SQLite operations. Manages the prompts table with support for queued, processing, and completed states.

- **static/index.html**: Self-contained web interface with vanilla JavaScript for prompt submission, status polling, and result display. Includes embedded CSS styling and requires no external dependencies. Features navigation menu for accessing all pages.

- **static/list.html**: Paginated list view showing all prompts in the queue with their status and timestamps. Auto-refreshes every 5 seconds and supports navigation between pages.

### Data

- **data/queue.db**: SQLite database (auto-created) containing the prompts table with columns for id, prompt, status, result, created_at, and updated_at.

## Installation

### Prerequisites

- Python 3.7 or higher
- Ollama installed and running locally (default: `http://localhost:11434`)
- The `llama3.2` model pulled in Ollama

### Setup

1. Clone or download the project:
   ```bash
   git clone <repository-url>
   cd ollama_proxy
   ```

2. Ensure Ollama is running and the model is available:
   ```bash
   ollama pull llama3.2
   ollama serve
   ```

3. No additional Python dependencies required - uses only standard library modules.

## Usage

### Starting the Proxy Server

Run the proxy server to handle API requests and serve the frontend:

```bash
python src/proxy.py
```

The server will start on `http://0.0.0.0:8000` by default.

### Starting the Worker

In a separate terminal, start the worker to process queued prompts:

```bash
python src/worker.py
```

The worker will continuously poll for new prompts and process them using the Ollama API.

### Using the Web Interface

1. Open your browser to `http://localhost:8000`
2. Enter your prompt in the text area
3. Click "Queue Prompt"
4. The interface will automatically poll for status updates and display the result when complete
5. Navigate to `http://localhost:8000/list` to view all prompts in the queue

### API Endpoints

#### Submit a Prompt

```bash
POST /api/v1/prompt
Content-Type: application/json

{
  "prompt": "Your question or prompt here"
}
```

Response:
```json
{
  "id": "uuid-string"
}
```

#### Check Prompt Status

```bash
GET /api/v1/prompt/{id}/status
```

Response:
```json
{
  "id": "uuid-string",
  "status": "queued|processing|completed"
}
```

#### Get Prompt Result

```bash
GET /api/v1/prompt/{id}/result
```

Response (when completed):
```json
{
  "id": "uuid-string",
  "status": "completed",
  "result": "The response from Ollama"
}
```

Response (when not completed):
```json
{
  "id": "uuid-string",
  "status": "queued|processing"
}
```

#### List All Prompts

```bash
GET /api/v1/prompts?page=1&page_size=5
```

Response:
```json
{
  "prompts": [
    {
      "id": "uuid-string",
      "status": "completed",
      "created_at": "2026-02-21T12:00:00+00:00",
      "updated_at": "2026-02-21T12:01:30+00:00"
    }
  ],
  "page": 1,
  "page_size": 5,
  "total": 10,
  "total_pages": 2
}
```

### Environment Variables

Configure the behavior using these optional environment variables:

- `OLLAMA_URL`: Ollama API endpoint (default: `http://localhost:11434/api/generate`)
- `OLLAMA_MODEL`: Model to use (default: `llama3.2`)
- `OLLAMA_POLL_INTERVAL`: Worker polling interval in seconds (default: `1.0`)
- `OLLAMA_PROXY_DB`: Custom path for SQLite database (default: `data/queue.db`)
- `OLLAMA_PROXY_QUIET`: Suppress request logs from proxy (set to any value to enable)

Example:
```bash
export OLLAMA_MODEL=llama3.2
export OLLAMA_POLL_INTERVAL=2.0
python src/proxy.py
```

### Example Usage with curl

Submit a prompt:
```bash
curl -X POST http://localhost:8000/api/v1/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

Check status:
```bash
curl http://localhost:8000/api/v1/prompt/{id}/status
```

Get result:
```bash
curl http://localhost:8000/api/v1/prompt/{id}/result
```

## Update Log

**2026-02-21**: Added prompt list view with pagination. New features include `/list` page showing all prompts in a table, `/api/v1/prompts` API endpoint with page and page_size query parameters (default: 5 per page, newest first), navigation menu on all pages, and auto-refresh every 5 seconds on the list page.

**2026-02-16**: Initial release with proxy server, worker, and web frontend. Features include SQLite queue management, RESTful API, status tracking, and caching disabled for fresh responses.
