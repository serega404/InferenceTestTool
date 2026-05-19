# InferenceTestTool

[🇬🇧 English](README.md) | [🇷🇺 Русский](README.RU.md)

Лёгкий терминальный бенчмарк для OpenAI-совместимых chat completion API.

---

## Что делает проект

`InferenceTestTool` периодически отправляет запросы в `/v1/chat/completions`, сохраняет результаты в CSV и показывает live-дашборд в терминале (через `curses`).

Инструмент помогает быстро оценивать:
- задержку ответа;
- скорость генерации токенов;
- тайминги prompt/generation, которые возвращает API;
- стабильность на длинных прогонах.

---

## Возможности

- OpenAI-совместимый POST-запрос в `INFERENCE_URL`
- Настройка через переменные окружения (без CLI-аргументов)
- Непрерывный цикл бенчмарка с настраиваемым интервалом
- Логирование в CSV для последующего анализа
- TUI-дашборд с:
  - статусом текущего теста
  - деталями последнего ответа
  - live-графиком выбранной метрики
  - агрегированной статистикой (avg/min/max)

---

## Требования

- Python 3.9+
- Зависимость:
  - `requests`
- API endpoint, совместимый с chat completions (`/v1/chat/completions`)

Установка зависимости:

```bash
pip install requests
```

---

## Быстрый старт

1. Клонируйте репозиторий:

```bash
git clone https://github.com/<your-org>/InferenceTestTool.git
cd InferenceTestTool
```

2. (Опционально) создайте виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Настройте переменные окружения (пример):

```bash
export INFERENCE_URL="http://localhost:8080/v1/chat/completions"
export MODEL_NAME="qwen3.6-35b-a3b-q5"
export PROMPT_CONTENT="Привет! Кратко объясни, что ты умеешь."
export MAX_TOKENS=256
export TEMPERATURE=0.6
export REQUEST_TIMEOUT_SECONDS=120
export LOOP_INTERVAL_SECONDS=5
export CSV_FILE="chat_benchmark.csv"
```

4. Запустите бенчмарк:

```bash
python bench_chat.py
```

---

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `INFERENCE_URL` | `http://localhost:8080/v1/chat/completions` | Целевой chat completion endpoint |
| `MODEL_NAME` | `qwen3.6-35b-a3b-q5` | Имя модели в payload |
| `PROMPT_CONTENT` | `Привет. Кратко объясни, что ты умеешь.` | Пользовательский prompt для каждого запроса |
| `MAX_TOKENS` | `256` | `max_tokens` в payload запроса |
| `TEMPERATURE` | `0.6` | `temperature` в payload запроса |
| `CONTENT_TYPE` | `application/json` | HTTP-заголовок `Content-Type` |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Таймаут одного HTTP-запроса |
| `LOOP_INTERVAL_SECONDS` | `5` | Пауза между итерациями бенчмарка |
| `CSV_FILE` | `chat_benchmark.csv` | Путь к выходному CSV |

> Важно: скрипт читает переменные через `os.getenv`. Если вы используете `.env`, экспортируйте переменные в shell перед запуском.

---

## Формат CSV

В CSV записываются колонки:

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

## Как считаются метрики

- `latency_ms`: фактическая wall-clock длительность запроса.
- `tokens_per_second`: `completion_tokens / latency_seconds`.
- `prompt_ms`, `predicted_ms`, `predicted_per_second`: значения из объекта API `timings` (если присутствуют).
- Если запрос завершается ошибкой, поле `error` заполняется, а строка всё равно сохраняется.

---

## Управление в TUI

Внутри дашборда можно переключать метрики графика и выходить из приложения.

Если управление отличается в вашей версии, проверьте обработку клавиш в `bench_chat.py` (поиск по `getch`).

---

## Типовые сценарии использования

- Сравнение скорости инференса до/после квантизации модели
- Мониторинг регрессий производительности API
- Стресс-проверка стабильности локального inference-сервера
- Сбор истории бенчмарков для отчётов

---

## Решение проблем

- **`ModuleNotFoundError: requests`**
  Установите зависимость: `pip install requests`.

- **Нет таймингов на графике (`prompt_ms`, `predicted_ms`)**
  Ваш backend может не возвращать `timings`. Используйте метрики `latency_ms` или `tokens_per_second`.

- **HTTP-ошибки (4xx/5xx)**
  Проверьте URL, имя модели, auth/proxy слой и совместимость payload.

- **Пустая/некорректная статистика токенов**
  Некоторые backend-реализации не возвращают стандартный объект `usage`, поэтому часть метрик может быть неполной.

---

## Лицензия

MIT (см. `LICENSE`).
