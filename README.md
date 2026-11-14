# Домашнее задание 3

## Структура репозитория

- `app/` — исходный код приложения, зависимости и документация.
- `Dockerfile` — инструкция для сборки Docker-образа.
- `compose.yaml` — описание сервиса и именованного тома.
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

## Проверка работы

Начальное состояние

```bash
curl -fsS http://127.0.0.1:8080/
```

```json
{"greeting": "hello", "count": 0, "hostname": "e93e304511a4", "storage": "sqlite"}
```

Увеличение счетчика

```bash
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS -X POST http://127.0.0.1:8080/increment
```

```json
{"greeting": "hello", "count": 3, "hostname": "e93e304511a4", "storage": "sqlite"}
```

Повторный get

```bash
curl -fsS http://127.0.0.1:8080/
```

```json
{"greeting": "hello", "count": 3, "hostname": "e93e304511a4", "storage": "sqlite"}
```

Проверка готовности

```bash
curl -fsS http://127.0.0.1:8080/readyz
```

```json
{"status": "ready", "storage": "sqlite"}
```

## Проверка сохранения данных

Удаляем контейнер без удаления тома

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
{"greeting": "hello", "count": 3, "hostname": "ac58cbd7fa7f", "storage": "sqlite"}
```

`count` остался равен 3.
