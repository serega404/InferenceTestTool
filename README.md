# InferenceTestTool

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.RU.md)

A lightweight terminal benchmark utility for OpenAI-compatible chat completion APIs.

---

## What this project does

`InferenceTestTool` sends periodic requests to a `/v1/chat/completions` endpoint, stores each run in CSV, and shows a live terminal dashboard with charts (via `curses`).

It helps you quickly evaluate:
- Response latency
- Token generation speed
- Prompt/generation timings returned by API
- Stability over long runs

---

## Features

- OpenAI-compatible POST request to `INFERENCE_URL`
- Environment-driven configuration (no CLI args required)
- Continuous benchmark loop with configurable interval
- CSV logging for later analysis
- TUI dashboard with:
  - Current test status
  - Last response details
  - Live chart for selected metric
  - Aggregate stats (avg/min/max)

---

## Requirements

- Python 3.9+
- Dependency:
  - `requests`
- API endpoint compatible with chat completions (`/v1/chat/completions`)

Install dependency:

```bash
pip install requests
```

---

## Quick start

1. Clone repository:

```bash
git clone https://github.com/<your-org>/InferenceTestTool.git
cd InferenceTestTool
```

2. (Optional) create virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Configure environment variables (example):

```bash
export INFERENCE_URL="http://localhost:8080/v1/chat/completions"
export MODEL_NAME="qwen3.6-35b-a3b-q5"
export PROMPT_CONTENT="Hello! Briefly tell me what you can do."
export MAX_TOKENS=256
export TEMPERATURE=0.6
export REQUEST_TIMEOUT_SECONDS=120
export LOOP_INTERVAL_SECONDS=5
export CSV_FILE="chat_benchmark.csv"
```

4. Run benchmark:

```bash
python bench_chat.py
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `INFERENCE_URL` | `http://localhost:8080/v1/chat/completions` | Target chat completion endpoint |
| `MODEL_NAME` | `qwen3.6-35b-a3b-q5` | Model name used in payload |
| `PROMPT_CONTENT` | `Привет. Кратко объясни, что ты умеешь.` | User prompt for each request |
| `MAX_TOKENS` | `256` | `max_tokens` in request payload |
| `TEMPERATURE` | `0.6` | `temperature` in request payload |
| `CONTENT_TYPE` | `application/json` | HTTP `Content-Type` header |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Timeout for one HTTP request |
| `LOOP_INTERVAL_SECONDS` | `5` | Delay between benchmark iterations |
| `CSV_FILE` | `chat_benchmark.csv` | Output CSV path |

> Note: script reads variables via `os.getenv`. If you use a `.env` file, export variables into the shell before running.

---

## Output CSV format

Columns written to CSV:

- `timestamp`
- `status_code`
- `finish_reason`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `latency_ms`
- `tokens_per_second`
- `prompt_ms`
- `predicted_ms`
- `predicted_per_second`
- `error`

---

## How metrics are calculated

- `latency_ms`: wall-clock request duration.
- `tokens_per_second`: `completion_tokens / latency_seconds`.
- `prompt_ms`, `predicted_ms`, `predicted_per_second`: values parsed from API `timings` object (if present).
- If request fails, `error` is populated and row is still saved.

---

## Keyboard controls (TUI)

Inside dashboard, you can switch chart metrics and exit.

If controls differ in your version, inspect key handling in `bench_chat.py` (search for `getch`).

---

## Typical usage scenarios

- Compare inference speed before/after model quantization
- Track API performance regressions
- Stress-check local inference server stability
- Gather benchmark history for reports

---

## Troubleshooting

- **`ModuleNotFoundError: requests`**
  Install dependency with `pip install requests`.

- **No timings in chart (`prompt_ms`, `predicted_ms`)**
  Your backend may not return `timings`. Use other metrics like `latency_ms` or `tokens_per_second`.

- **HTTP errors (4xx/5xx)**
  Verify URL, model name, auth/proxy layer, and payload compatibility.

- **Empty/invalid token stats**
  Some backends do not return standard `usage`. Script handles missing fields, but metrics may be incomplete.

---

## License

MIT License (see `LICENSE`).
