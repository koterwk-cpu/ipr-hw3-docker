# Домашнее задание 3

## Структура репозитория

- `app/` — исходный код приложения, зависимости и документация (без изменений).
- `Dockerfile` — инструкция для сборки Docker-образа.
- `.dockerignore` — исключение лишних файлов из контекста сборки.
- `.gitignore` — игнорирование `.env`, `backups/` и временных файлов.
- `compose.yaml` — описание сервисов `app` и `redis`, тома, healthcheck и ограничений.
- `.env.example` — шаблон переменных окружения.
- `scripts/check.py` — автоматическая проверка восстановления.
- `logs.txt` — логи приложения, сохраняются скриптом проверки.
- `backups/` — резервные копии, создаётся скриптом (добавлена в `.gitignore`).

## Переменные окружения

Значения по умолчанию лежат в `.env.example`. Перед первым запуском скопируйте шаблон:

```
cp .env.example .env
```

```
GREETING=hello
HOST_PORT=8080
PORT=8000
STORAGE=redis
REDIS_URL=redis://redis:6379/0
```

Скрипт `scripts/check.py` создаёт `.env` из шаблона автоматически, если его нет.

## Ограничения процесса

- Процесс `app` работает от UID 10001 (не root).
- Корневая файловая система `app` доступна только для чтения (`read_only: true`, временные файлы через `tmpfs` в `/tmp`).
- Лимиты `app`: не больше 256 MiB RAM и 1 ядра CPU.

## Запуск

Сборка образа и запуск выполняются из корня репозитория:

```
cp .env.example .env
docker compose up -d --build
```

Проверка статуса:

```
docker compose ps
```

```
NAME                     IMAGE                COMMAND                  SERVICE   STATUS                           PORTS
ipr-hw3-docker-app-1     ipr-hw3-docker-app   "python app.py"          app       Up 1 second (health: starting)   0.0.0.0:8080->8000/tcp
ipr-hw3-docker-redis-1   redis:7.4-alpine     "docker-entrypoint.s…"   redis     Up 12 seconds (healthy)          6379/tcp
```

## Проверка одного контейнера

```
docker build -t hw3-app .
docker run -d --name hw3-counter -p 8080:8000 -e GREETING="hello" -e DATA_FILE=/tmp/counter.db hw3-app
curl -fsS http://127.0.0.1:8080/
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS http://127.0.0.1:8080/
curl -fsS http://127.0.0.1:8080/readyz
docker logs hw3-counter
docker rm -f hw3-counter
```

## Проверка хранилища Redis

Начальное состояние

```
curl -fsS http://127.0.0.1:8080/
```

```
{"greeting": "hello", "count": 0, "hostname": "7bac9bfb971c", "storage": "redis"}
```

Увеличение счетчика

```
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS -X POST http://127.0.0.1:8080/increment
curl -fsS -X POST http://127.0.0.1:8080/increment
```

```
{"greeting": "hello", "count": 1, "hostname": "7bac9bfb971c", "storage": "redis"}
{"greeting": "hello", "count": 2, "hostname": "7bac9bfb971c", "storage": "redis"}
{"greeting": "hello", "count": 3, "hostname": "7bac9bfb971c", "storage": "redis"}
```

Повторный get

```
curl -fsS http://127.0.0.1:8080/
```

```
{"greeting": "hello", "count": 3, "hostname": "7bac9bfb971c", "storage": "redis"}
```

Проверка готовности

```
curl -fsS http://127.0.0.1:8080/readyz
```

```
{"status": "ready", "storage": "redis"}
```

Удаляем контейнеры без удаления тома

```
docker compose down
```

Поднимаем заново

```
docker compose up -d
```

Проверяем счётчик

```
curl -fsS http://127.0.0.1:8080/
```

```
{"greeting": "hello", "count": 3, "hostname": "17eddd139be5", "storage": "redis"}
```

`hostname` изменился, контейнер новый, `count` остался равен 3.

Останавливаем Redis

```
docker compose stop redis
```

Приложение живо, /healthz отвечает 200

```
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8080/healthz
```

```
{"status": "alive"}
200
```

Хранилище недоступно, /readyz отвечает 503

```
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8080/readyz
```

```
{"error": "storage_unavailable"}
503
```

Инкремент тоже отвечает 503

```
curl -s -w "\n%{http_code}\n" -X POST http://127.0.0.1:8080/increment
```

```
{"error": "storage_unavailable"}
503
```

Запускаем Redis обратно

```
docker compose start redis
```

Ждём готовности

```
docker compose ps
```

Счётчик вернулся к прежнему значению

```
curl -fsS http://127.0.0.1:8080/
```

```
{"greeting": "hello", "count": 3, "hostname": "17eddd139be5", "storage": "redis"}
```

Инкремент работает

```
curl -fsS -X POST http://127.0.0.1:8080/increment
```

```
{"greeting": "hello", "count": 4, "hostname": "17eddd139be5", "storage": "redis"}
```

Логи приложения в этот момент

```
2026-11-14 13:49:32,924 listening port=8000 storage=redis
2026-11-14 13:49:36,715 http 127.0.0.1 "GET /healthz HTTP/1.1" 200 -
2026-11-14 13:49:41,965 http 172.18.0.1 "GET / HTTP/1.1" 200 -
2026-11-14 13:49:46,767 http 127.0.0.1 "GET /healthz HTTP/1.1" 200 -
2026-11-14 13:49:47,925 http 172.18.0.1 "GET /healthz HTTP/1.1" 200 -
2026-11-14 13:49:47,953 storage_unavailable: ConnectionError
2026-11-14 13:49:47,953 http 172.18.0.1 "GET /readyz HTTP/1.1" 503 -
2026-11-14 13:49:47,978 storage_unavailable: ConnectionError
2026-11-14 13:49:47,978 http 172.18.0.1 "POST /increment HTTP/1.1" 503 -
2026-11-14 13:49:53,532 http 172.18.0.1 "GET / HTTP/1.1" 200 -
2026-11-14 13:49:53,544 http 172.18.0.1 "POST /increment HTTP/1.1" 200 -
2026-11-14 13:49:56,813 http 127.0.0.1 "GET /healthz HTTP/1.1" 200 -
```

## Автоматическая проверка

Скрипт `scripts/check.py`. Запуск из корня репозитория:

```
python3 scripts/check.py
```

Первый запуск:

```
== initialization
[+] Building 32.3s (14/14) FINISHED
 => [internal] load local bake definitions 0.0s
 => => reading from stdin 538B 0.0s
 => [internal] load build definition from Dockerfile 0.1s
 => => transferring dockerfile: 424B 0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim 2.1s
 => [internal] load .dockerignore 0.0s
 => => transferring context: 184B 0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.2s
 => => resolve docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.2s
 => [internal] load build context 0.1s
 => => transferring context: 5.96kB 0.0s
 => CACHED [2/7] WORKDIR /app 0.0s
 => [3/7] RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* 22.2s
 => [4/7] RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser 0.5s
 => [5/7] COPY app/requirements.txt . 0.1s
 => [6/7] RUN pip install --no-cache-dir -r requirements.txt 4.3s
 => [7/7] COPY app . 0.1s
 => exporting to image 1.4s
 => => exporting layers 0.9s
 => => exporting manifest sha256:719bf36f678ec14ff3c504f56f695c8d6dde69a359a902c654f8145cb53a258a 0.0s
 => => exporting config sha256:da2b1002a96ea84d6acb3e6cd98686316276b8c2c543c2a4205b0db988b413a8 0.0s
 => => exporting attestation manifest sha256:27353c86b64523d524cd1d3a8f5fda17489bb6131cf9ca179410cc974bfd4795 0.0s
 => => exporting manifest list sha256:e5b9dc5d32c4ac48dda4b627c1fc872e91a8e58b3680d34db9c8fcca30cca647 0.0s
 => => naming to docker.io/library/hw3-test-115845-1794686466-app:latest 0.0s
 => => unpacking to docker.io/library/hw3-test-115845-1794686466-app:latest 0.4s
 => resolving provenance for metadata file 0.0s
[+] up 5/5
 ✔ Image hw3-test-115845-1794686466-app         Built    32.7s
 ✔ Network hw3-test-115845-1794686466_default   Created  0.8s
 ✔ Volume hw3-test-115845-1794686466_redis_data Created  0.0s
 ✔ Container hw3-test-115845-1794686466-redis-1 Healthy  11.9s
 ✔ Container hw3-test-115845-1794686466-app-1   Started  12.6s
== check counter
== check save data in app down
[+] up 1/1
 ✔ Container hw3-test-115845-1794686466-app-1 Started 11.8s
== stop redis
[+] stop 1/1
 ✔ Container hw3-test-115845-1794686466-redis-1 Stopped 0.4s
== redis start again
[+] start 1/1
 ✔ Container hw3-test-115845-1794686466-redis-1 Started 0.6s
== consistent backup
[+] stop 2/2
 ✔ Container hw3-test-115845-1794686466-redis-1 Stopped 0.4s
 ✔ Container hw3-test-115845-1794686466-app-1   Stopped 10.8s
== collect logs
== cleanup
Test passed
```

Второй запуск подряд:

```
== initialization
[+] Building 1.6s (14/14) FINISHED
 => [internal] load local bake definitions 0.0s
 => => reading from stdin 538B 0.0s
 => [internal] load build definition from Dockerfile 0.0s
 => => transferring dockerfile: 424B 0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim 0.8s
 => [internal] load .dockerignore 0.0s
 => => transferring context: 184B 0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.0s
 => => resolve docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.0s
 => [internal] load build context 0.0s
 => => transferring context: 127B 0.0s
 => CACHED [2/7] WORKDIR /app 0.0s
 => CACHED [3/7] RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* 0.0s
 => CACHED [4/7] RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser 0.0s
 => CACHED [5/7] COPY app/requirements.txt . 0.0s
 => CACHED [6/7] RUN pip install --no-cache-dir -r requirements.txt 0.0s
 => CACHED [7/7] COPY app . 0.0s
 => exporting to image 0.5s
 => => exporting layers 0.0s
 => => exporting manifest sha256:eb905cf3cd8b7aa6f42131ec8125e312be4a11837e7e930aa3005c3faa302517 0.0s
 => => exporting config sha256:e138751a609bafd4530017c1c1b9e9852d756f453374fdd0b7b46c7c679b1330 0.0s
 => => exporting attestation manifest sha256:fd74c084ee2a7363aa1c9495fdf3cd95e7248e3b719b4367013d735c1b149e02 0.0s
 => => exporting manifest list sha256:1effe50261015b27c58451976cac63efd57ffa8e6fa1875779a45cee65de31ad 0.0s
 => => naming to docker.io/library/hw3-test-119292-1794686564-app:latest 0.0s
 => => unpacking to docker.io/library/hw3-test-119292-1794686564-app:latest 0.3s
 => resolving provenance for metadata file 0.0s
[+] up 5/5
 ✔ Image hw3-test-119292-1794686564-app         Built    1.7s
 ✔ Volume hw3-test-119292-1794686564_redis_data Created  0.0s
 ✔ Network hw3-test-119292-1794686564_default   Created  0.6s
 ✔ Container hw3-test-119292-1794686564-redis-1 Healthy  11.3s
 ✔ Container hw3-test-119292-1794686564-app-1   Started  12.2s
== check counter
== check save data in app down
[+] up 1/1
 ✔ Container hw3-test-119292-1794686564-app-1 Started 11.4s
== stop redis
[+] stop 1/1
 ✔ Container hw3-test-119292-1794686564-redis-1 Stopped 0.4s
== redis start again
[+] start 1/1
 ✔ Container hw3-test-119292-1794686564-redis-1 Started 0.6s
== consistent backup
[+] stop 2/2
 ✔ Container hw3-test-119292-1794686564-app-1   Stopped 10.7s
 ✔ Container hw3-test-119292-1794686564-redis-1 Stopped 0.4s
== collect logs
== cleanup
Test passed
```

Резервная копия сохраняется в `backups/redis-backup.tar.gz`.

## Логи

Скрипт проверки автоматически сохраняет логи приложения в `logs.txt`.