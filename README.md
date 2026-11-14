# Домашнее задание 3

## Структура репозитория

- `app/` — исходный код приложения, зависимости и документация.
- `Dockerfile` — инструкция для сборки Docker-образа.
- `.dockerignore` — исключение лишних файлов из контекста сборки.
- `.gitignore` — игнорирование `.env`, `backups/` и временных файлов.
- `compose.yaml` — описание сервисов `app` и `redis`, тома, healthcheck и ограничений.
- `.env.example` — шаблон переменных окружения.
- `scripts/check.py` — автоматическая проверка восстановления.
- `logs.txt` — логи приложения, сохраняются скриптом проверки.
- `backups/` — резервные копии, создаётся скриптом (добавлена в `.gitignore`).

## Переменные окружения

Переменные лежат в .env, пример переменных в .env.example

```env
GREETING=hello
HOST_PORT=8080
PORT=8000
STORAGE=redis
REDIS_URL=redis://redis:6379/0
```

## Ограничения процесса

- Процесс `app` работает от UID 10001 (не root).
- Корневая файловая система `app` доступна только для чтения (`read_only: true`, временные файлы через `tmpfs` в `/tmp`).
- Лимиты `app`: не больше 256 MiB RAM и 1 ядра CPU.

## Запуск

Сборка образа и запуск выполняются одной командой из корня репозитория:

```bash
docker compose up -d --build
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

## Автоматическая проверка

Скрипт `scripts/check.py`. Запуск из корня репозитория:

```bash
python3 scripts/check.py
```

Первый запуск:

```text
== initialization
[+] Building 3.0s (14/14) FINISHED
 => [internal] load local bake definitions 0.0s
 => => reading from stdin 538B 0.0s
 => [internal] load build definition from Dockerfile 0.0s
 => => transferring dockerfile: 392B 0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim 1.6s
 => [internal] load .dockerignore 0.0s
 => => transferring context: 34B 0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.1s
 => => resolve docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.1s
 => [internal] load build context 0.1s
 => => transferring context: 127B 0.0s
 => CACHED [2/7] WORKDIR /app 0.0s
 => CACHED [3/7] RUN apt-get update && apt-get install -y --no-install-recommends curl 0.0s
 => CACHED [4/7] RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser 0.0s
 => CACHED [5/7] COPY app/requirements.txt . 0.0s
 => CACHED [6/7] RUN pip install --no-cache-dir -r requirements.txt 0.0s
 => CACHED [7/7] COPY app . 0.0s
 => exporting to image 0.4s
 => => exporting layers 0.1s
 => => exporting manifest sha256:4014fb1fdcd28efee3e76d3315a60d22bb958e7b264959136656801f2904cb37 0.0s
 => => exporting config sha256:3d3b84eb2e2b59cc0c85b2cbb2d41b6922a6aa577ffa75194820b2296d0d8efc 0.0s
 => => exporting attestation manifest sha256:87785b35e13d61117c6c13a326c2111e890d9e084ca04560f1556b3f93e11490 0.0s
 => => exporting manifest list sha256:51fb88a84358bb672a90b5fbf1416801821dca71a613161ca6f59468bda57917 0.0s
 => => naming to docker.io/library/hw3-test-108609-1794681270-app:latest 0.0s
 => => unpacking to docker.io/library/hw3-test-108609-1794681270-app:latest 0.0s
 => resolving provenance for metadata file 0.0s
[+] up 5/5
 ✔ Image hw3-test-108609-1794681270-app Built 3.2s
 ✔ Network hw3-test-108609-1794681270_default Created 0.8s
 ✔ Volume hw3-test-108609-1794681270_redis_data Created 0.0s
 ✔ Container hw3-test-108609-1794681270-redis-1 Healthy 11.7s
 ✔ Container hw3-test-108609-1794681270-app-1 Started 12.4s
== check counter
== check save data in app down
[+] up 1/1
 ✔ Container hw3-test-108609-1794681270-app-1 Started 11.5s
== stop redis
[+] stop 1/1
 ✔ Container hw3-test-108609-1794681270-redis-1 Stopped 0.5s
== redis start again
[+] start 1/1
 ✔ Container hw3-test-108609-1794681270-redis-1 Started 0.5s
== consistent backup
[+] stop 2/2
 ✔ Container hw3-test-108609-1794681270-redis-1 Stopped 0.3s
 ✔ Container hw3-test-108609-1794681270-app-1 Stopped 10.5s
Unable to find image 'alpine:3.20' locally
3.20: Pulling from library/alpine
25f1d6b1951a: Pull complete
3a030ca3f633: Download complete
d4050d56ebf2: Download complete
Digest: sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc
Status: Downloaded newer image for alpine:3.20
== collect logs
== cleanup
Test passed
```

Второй запуск подряд:

```text
== initialization
[+] Building 2.3s (14/14) FINISHED
 => [internal] load local bake definitions 0.0s
 => => reading from stdin 538B 0.0s
 => [internal] load build definition from Dockerfile 0.0s
 => => transferring dockerfile: 392B 0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim 1.3s
 => [internal] load .dockerignore 0.0s
 => => transferring context: 34B 0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.1s
 => => resolve docker.io/library/python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 0.0s
 => [internal] load build context 0.1s
 => => transferring context: 127B 0.0s
 => CACHED [2/7] WORKDIR /app 0.0s
 => CACHED [3/7] RUN apt-get update && apt-get install -y --no-install-recommends curl 0.0s
 => CACHED [4/7] RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser 0.0s
 => CACHED [5/7] COPY app/requirements.txt . 0.0s
 => CACHED [6/7] RUN pip install --no-cache-dir -r requirements.txt 0.0s
 => CACHED [7/7] COPY app . 0.0s
 => exporting to image 0.2s
 => => exporting layers 0.0s
 => => exporting manifest sha256:25561552352ade743f1efb42b514c0129eb985e065f3bd058dab6c7b9702c914 0.0s
 => => exporting config sha256:d9ac916bd5cb8665743322b17e0a8917d3887dc36e16e4ab609010f4680e90bd 0.0s
 => => exporting attestation manifest sha256:eb02fb95acba97010c3f68673e22fc3534d65b983463a9d9a32cd326d3a5186f 0.0s
 => => exporting manifest list sha256:68b387cc31cfaf0bdfc044981a834fd6e147b13b8946960197f93b80c0528f27 0.0s
 => => naming to docker.io/library/hw3-test-111401-1794681553-app:latest 0.0s
 => => unpacking to docker.io/library/hw3-test-111401-1794681553-app:latest 0.0s
 => resolving provenance for metadata file 0.0s
[+] up 5/5
 ✔ Image hw3-test-111401-1794681553-app Built 2.5s
 ✔ Network hw3-test-111401-1794681553_default Created 0.9s
 ✔ Volume hw3-test-111401-1794681553_redis_data Created 0.0s
 ✔ Container hw3-test-111401-1794681553-redis-1 Healthy 11.5s
 ✔ Container hw3-test-111401-1794681553-app-1 Started 12.1s
== check counter
== check save data in app down
[+] up 1/1
 ✔ Container hw3-test-111401-1794681553-app-1 Started 11.4s
== stop redis
[+] stop 1/1
 ✔ Container hw3-test-111401-1794681553-redis-1 Stopped 0.4s
== redis start again
[+] start 1/1
 ✔ Container hw3-test-111401-1794681553-redis-1 Started 0.6s
== consistent backup
[+] stop 2/2
 ✔ Container hw3-test-111401-1794681553-app-1 Stopped 10.6s
 ✔ Container hw3-test-111401-1794681553-redis-1 Stopped 0.4s
== collect logs
== cleanup
Test passed
```

## Логи

Скрипт проверки автоматически сохраняет логи приложения в `logs.txt`.