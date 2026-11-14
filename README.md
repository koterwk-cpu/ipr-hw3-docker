# Домашнее задание 3

## Структура репозитория

- `app/` — исходный код приложения, зависимости и документация.
- `Dockerfile` — инструкция для сборки Docker-образа.
- `compose.yaml` — описание сервисов `app` и `redis`, тома и healthcheck.
- `.env.example` — шаблон переменных окружения.
- `logs.txt` — вывод логов работающего контейнера.

## Переменные окружения

Переменные лежат в .env, пример переменных в .env.example

## Запуск

Сборка образа и запуск выполняются одной командой из корня репозитория:

```bash
docker compose up -d
```

Проверка статуса:

```bash
docker compose ps
```

```text
NAME                     IMAGE                COMMAND                  SERVICE   STATUS                           PORTS
ipr-hw3-docker-app-1     ipr-hw3-docker-app   "python app.py"          app       Up 1 second (health: starting)   0.0.0.0:8080->8000/tcp
ipr-hw3-docker-redis-1   redis:7.4-alpine     "docker-entrypoint.s…"   redis     Up 12 seconds (healthy)          6379/tcp
```

## Проверка работы

Начальное состояние

```bash
curl -fsS http://127.0.0.1:8080/
```

```json
{"greeting": "hello", "count": 0, "hostname": "7bac9bfb971c", "storage": "redis"}
```

Увеличение счетчика

```bash
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS -X POST http://127.0.0.1:8080/increment
```

```json
{"greeting": "hello", "count": 1, "hostname": "7bac9bfb971c", "storage": "redis"}
{"greeting": "hello", "count": 2, "hostname": "7bac9bfb971c", "storage": "redis"}
{"greeting": "hello", "count": 3, "hostname": "7bac9bfb971c", "storage": "redis"}
```

Повторный get

```bash
curl -fsS http://127.0.0.1:8080/
```

```json
{"greeting": "hello", "count": 3, "hostname": "7bac9bfb971c", "storage": "redis"}
```

Проверка готовности

```bash
curl -fsS http://127.0.0.1:8080/readyz
```

```json
{"status": "ready", "storage": "redis"}
```

## Проверка сохранения данных

Удаляем контейнеры без удаления тома

```bash
docker compose down
```

Поднимаем заново

```bash
docker compose up -d
```

Проверяем счётчик

```bash
curl -fsS http://127.0.0.1:8080/
```

```json
{"greeting": "hello", "count": 3, "hostname": "17eddd139be5", "storage": "redis"}
```

`hostname` изменился, контейнер новый, `count` остался равен 3.

## Проверка при недоступном Redis

Останавливаем Redis

```bash
docker compose stop redis
```

Приложение живо, /healthz отвечает 200

```bash
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8080/healthz
```

```text
{"status": "alive"}
200
```

Хранилище недоступно, /readyz отвечает 503

```bash
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8080/readyz
```

```text
{"error": "storage_unavailable"}
503
```

Инкремент тоже отвечает 503

```bash
curl -s -w "\n%{http_code}\n" -X POST http://127.0.0.1:8080/increment
```

```text
{"error": "storage_unavailable"}
503
```

## Проверка восстановления

Запускаем Redis обратно

```bash
docker compose start redis
```

Ждём готовности

```bash
docker compose ps
```

Счётчик вернулся к прежнему значению

```bash
curl -fsS http://127.0.0.1:8080/
```

```json
{"greeting": "hello", "count": 3, "hostname": "17eddd139be5", "storage": "redis"}
```

Инкремент работает

```bash
curl -fsS -X POST http://127.0.0.1:8080/increment
```

```json
{"greeting": "hello", "count": 4, "hostname": "17eddd139be5", "storage": "redis"}
```

## Логи

```bash
docker compose logs --no-log-prefix app > logs.txt
```

Логи лежат в log.txt