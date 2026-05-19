#!/usr/bin/env python3
import curses
import csv
import json
import time
from datetime import datetime
from pathlib import Path

import requests


URL = "http://localhost:8080/v1/chat/completions"
CSV_FILE = Path("chat_benchmark.csv")

PAYLOAD = {
    "model": "qwen3.6-35b-a3b-q5",
    "messages": [
        {
            "role": "user",
            "content": "Привет. Кратко объясни, что ты умеешь."
        }
    ],
    "max_tokens": 256,
    "temperature": 0.6,
}

HEADERS = {
    "Content-Type": "application/json"
}

CSV_FIELDS = [
    "timestamp",
    "status_code",
    "finish_reason",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "latency_ms",
    "tokens_per_second",
    "prompt_ms",
    "predicted_ms",
    "predicted_per_second",
    "error",
]

METRICS = {
    "tokens_per_second": {
        "label": "Скорость генерации",
        "unit": "tok/s",
    },
    "latency_ms": {
        "label": "Общая задержка",
        "unit": "ms",
    },
    "prompt_ms": {
        "label": "Обработка prompt",
        "unit": "ms",
    },
    "predicted_ms": {
        "label": "Время генерации",
        "unit": "ms",
    },
    "predicted_per_second": {
        "label": "Скорость генерации API",
        "unit": "tok/s",
    },
    "completion_tokens": {
        "label": "Сгенерированные токены",
        "unit": "tokens",
    },
    "total_tokens": {
        "label": "Всего токенов",
        "unit": "tokens",
    },
}


def ensure_csv():
    if not CSV_FILE.exists():
        with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_FIELDS)


def append_csv(result):
    with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(result)


def to_float(value, default=0.0):
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def run_test():
    started = time.perf_counter()
    timestamp = datetime.now().isoformat(timespec="seconds")

    result = {
        "timestamp": timestamp,
        "status_code": "",
        "finish_reason": "",
        "prompt_tokens": "",
        "completion_tokens": "",
        "total_tokens": "",
        "latency_ms": "",
        "tokens_per_second": "",
        "prompt_ms": "",
        "predicted_ms": "",
        "predicted_per_second": "",
        "error": "",
    }

    try:
        response = requests.post(
            URL,
            headers=HEADERS,
            data=json.dumps(PAYLOAD, ensure_ascii=False).encode("utf-8"),
            timeout=120,
        )

        latency_ms = (time.perf_counter() - started) * 1000
        result["status_code"] = response.status_code
        result["latency_ms"] = round(latency_ms, 2)

        data = response.json()

        usage = data.get("usage", {})
        timings = data.get("timings", {})
        choices = data.get("choices", [])

        prompt_tokens = usage.get("prompt_tokens", "")
        completion_tokens = usage.get("completion_tokens", "")
        total_tokens = usage.get("total_tokens", "")

        result["finish_reason"] = (
            choices[0].get("finish_reason", "") if choices else ""
        )

        result["prompt_tokens"] = prompt_tokens
        result["completion_tokens"] = completion_tokens
        result["total_tokens"] = total_tokens

        result["prompt_ms"] = round(to_float(timings.get("prompt_ms")), 2)
        result["predicted_ms"] = round(to_float(timings.get("predicted_ms")), 2)
        result["predicted_per_second"] = round(
            to_float(timings.get("predicted_per_second")),
            3,
        )

        completion_tokens_number = to_float(completion_tokens)

        if latency_ms > 0:
            result["tokens_per_second"] = round(
                completion_tokens_number / (latency_ms / 1000),
                3,
            )

    except Exception as e:
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        result["error"] = str(e)

    append_csv(result)
    return result


def get_metric_info(metric):
    return METRICS.get(metric, {
        "label": metric,
        "unit": "",
    })


def format_value(value, unit):
    value = to_float(value)

    if unit == "ms":
        return f"{value:.2f} ms"

    if unit == "tok/s":
        return f"{value:.2f} tok/s"

    if unit == "tokens":
        return f"{int(value)} tokens"

    return f"{value:.2f}"


def draw_chart(stdscr, results, metric):
    height, width = stdscr.getmaxyx()

    chart_height = min(12, max(6, height // 3))
    chart_width = max(20, width - 20)

    metric_info = get_metric_info(metric)
    label = metric_info["label"]
    unit = metric_info["unit"]

    values = []
    for r in results[-chart_width:]:
        values.append(to_float(r.get(metric), 0.0))

    if not values:
        stdscr.addstr(0, 2, "График появится после первого теста")
        return chart_height + 1

    min_value = min(values)
    max_value = max(values)

    if max_value == min_value:
        padding = max(abs(max_value) * 0.1, 1.0)
        min_value -= padding
        max_value += padding

    value_range = max_value - min_value

    plot = [[" " for _ in range(len(values))] for _ in range(chart_height)]

    for x, value in enumerate(values):
        normalized = (value - min_value) / value_range
        y = chart_height - 1 - round(normalized * (chart_height - 1))
        y = max(0, min(chart_height - 1, y))
        plot[y][x] = "●"

    title = (
        f"{label} ({unit}) | "
        f"min={format_value(min_value, unit)} | "
        f"max={format_value(max_value, unit)} | "
        f"points={len(values)}"
    )

    stdscr.addstr(0, 2, title[:width - 4])

    for row in range(chart_height):
        value = max_value - (row / max(1, chart_height - 1)) * value_range
        value_label = format_value(value, unit)

        line = "".join(plot[row])
        graph_line = f"{value_label:>14} │ {line}"

        stdscr.addstr(row + 1, 2, graph_line[:width - 4])

    axis_y = chart_height + 1
    axis = " " * 15 + "└" + "─" * min(len(values), chart_width)
    stdscr.addstr(axis_y, 2, axis[:width - 4])

    return chart_height + 3


def draw_ui(stdscr, results, running=False, metric="tokens_per_second"):
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    chart_bottom = draw_chart(stdscr, results, metric)

    y = chart_bottom + 1

    help_line = (
        "SPACE — тест | "
        "1 — tok/s | "
        "2 — latency ms | "
        "3 — prompt ms | "
        "4 — generation ms | "
        "5 — API tok/s | "
        "6 — completion tokens | "
        "q — выход"
    )

    stdscr.addstr(y, 2, help_line[:width - 4])
    y += 2

    if running:
        stdscr.addstr(y, 2, "Тест выполняется...")
        stdscr.refresh()
        return

    if not results:
        stdscr.addstr(y, 2, "Нажми пробел, чтобы запустить первый тест.")
        stdscr.refresh()
        return

    last = results[-1]

    rows = [
        ("Время", last["timestamp"]),
        ("HTTP status", last["status_code"]),
        ("Finish reason", last["finish_reason"]),
        ("Prompt tokens", f'{last["prompt_tokens"]} tokens'),
        ("Completion tokens", f'{last["completion_tokens"]} tokens'),
        ("Total tokens", f'{last["total_tokens"]} tokens'),
        ("Latency", format_value(last["latency_ms"], "ms")),
        ("Measured speed", format_value(last["tokens_per_second"], "tok/s")),
        ("Prompt time", format_value(last["prompt_ms"], "ms")),
        ("Generation time", format_value(last["predicted_ms"], "ms")),
        ("API speed", format_value(last["predicted_per_second"], "tok/s")),
        ("CSV file", str(CSV_FILE)),
    ]

    if last.get("error"):
        rows.append(("Error", last["error"]))

    for key, value in rows:
        if y >= height - 1:
            break

        line = f"{key:22} {value}"
        stdscr.addstr(y, 2, line[:width - 4])
        y += 1

    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    ensure_csv()

    results = []
    metric = "tokens_per_second"

    while True:
        draw_ui(stdscr, results, metric=metric)

        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            break

        elif key == ord("1"):
            metric = "tokens_per_second"

        elif key == ord("2"):
            metric = "latency_ms"

        elif key == ord("3"):
            metric = "prompt_ms"

        elif key == ord("4"):
            metric = "predicted_ms"

        elif key == ord("5"):
            metric = "predicted_per_second"

        elif key == ord("6"):
            metric = "completion_tokens"

        elif key == ord(" "):
            draw_ui(stdscr, results, running=True, metric=metric)
            result = run_test()
            results.append(result)


if __name__ == "__main__":
    curses.wrapper(main)
