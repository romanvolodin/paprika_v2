# Настройка VPS

Это инструкция как настроить чистый сервер перед запуском Паприки: выбор VPS, создание пользователя, базовая защита, проверка DNS.

Если сервер уже готов — переходите к [установке Паприки](production-run.md).

## Минимальные требования к серверу

- **2 ГБ RAM** — для запуска приложения достаточно и 512 Мб, но для сборки контейнеров прямо на сервере требуется больше оперативной памяти.
- **1 vCPU** достаточно для команды из нескольких человек; сборка образов просто займёт чуть больше времени.
- **20 ГБ диска** с запасом — сами образы небольшие, но база данных и загруженные файлы со временем потребуют больше места. (TODO: нужна инструкция для подключения отдельного диска для загруженных файлов.)
- **Публичный IPv4-адрес** и возможность открыть порты **80/443**.

## Операционная система

Всё приложение работает в Docker, так что подойдет любая операционная система, где можно запустить Docker. Для разработки Паприки в основном используется Ubuntu, поэтому все команды будут приведены для этой ОС.

## Создание пользователя

Большинство VPS выдают доступ пользователю `root` по паролю — это стоит поменять при первом же подключении. Создадим пользователя и настроим доступ по SSH.

Имя пользователя может быть любым, я назову `rika` (потому что pap**rika**).

Подключитесь к серверу как `root` и выполните команды:

```bash
adduser rika
usermod -aG sudo rika
```

Скопируйте свой SSH-ключ на сервер. (TODO: нужна инструкция по созданию ключа.)

На локальной машине выполните:

```bash
ssh-copy-id rika@ваш-сервер
```

!!! warning "Важно"

    Убедитесь, что можете зайти под новым пользователем и получить root через `sudo`, и только после этого отключайте пароль и root-логин по SSH.

    Не отключаясь от сервера, **в новом терминале** на локальной машине выполните `ssh rika@ваш-сервер`. Также попробуйте выполнить команду, которая требует `sudo`, например `sudo apt update`.

Теперь настроим подключение к серверу по SSH.

Откройте файл дополнительных настроек SSH. Для этого на сервере выполните:

```bash
nano /etc/ssh/sshd_config.d/hardening.conf
```

Добавьте следующие строчки в файл:

```bash
PasswordAuthentication no
PermitRootLogin no
MaxAuthTries 3
AllowUsers rika
```

`AllowUsers` — явный список пользователей, кому вообще можно логиниться по SSH; полезно если на сервере вдруг заведётся ещё один системный аккаунт с доступом.

Перезапускаем SSH:

```bash
sudo systemctl restart ssh
```

Дальше все команды выполняются от пользователя `rika` с использованием `sudo`, где необходимо.

## Автоматические обновления безопасности

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

Патчи безопасности ОС ставятся сами, без ручного запуска `apt upgrade`. Docker-контейнеры это не трогает — это только пакеты самой ОС.

## Файрвол

```bash
sudo apt update && sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Больше ничего открывать не нужно — ни Postgres, ни бэкенд не публикуют портов на хост, наружу смотрит только Caddy.

## Docker

Официальный способ установки (пакеты из репозитория Ubuntu/Debian часто
устаревшие):

```bash
# удалить возможные старые версии
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Проверьте, что стоит именно плагин-версия Compose (команда `docker compose`,
без дефиса — так называет её и `justfile`):

```bash
docker compose version
```

Чтобы не писать `sudo` перед каждой командой:

```bash
sudo usermod -aG docker rika
```

(потребует перелогиниться). Стоит знать: членство в группе `docker` фактически равносильно root-доступу на хосте — это стандартный компромисс для удобства, а не дыра, которую я упустил.

Изредка стоит подтягивать патчи безопасности и в базовые образы (`postgres:18-alpine`, `caddy:2-alpine`), на которых собраны наши образы — `just run`/`just update` этого сами не делают, если слой в кэше:

```bash
docker compose -f compose.prod.yaml build --pull
```

Логи контейнеров уже ограничены по размеру (`compose.prod.yaml`, `logging:` — 10 МБ × 3 файла на сервис) — без этого у Docker `json-file` драйвер по умолчанию ничем не ограничен и со временем может забить диск.

## `just`

```bash
sudo apt install -y just
```

Если в репозитории вашего дистрибутива версия слишком старая или её нет — [официальные варианты установки](https://github.com/casey/just#installation).

## DNS

Заведите A-запись домена на IP этого сервера ещё до первого запуска — Caddy получает сертификат от Let's Encrypt автоматически при первом обращении, но для этого домен уже должен резолвиться на сервер. Проверить:

```bash
dig +short ваш-домен.example.com
```

должно вернуть тот же IP, что у сервера.

## Дополнительные проверки (опционально)

```bash
sudo apt install -y lynis
sudo lynis audit system
```

Не обязательно, но полезно — `lynis` читает конфигурацию сервера и показывает список типовых рекомендаций по безопасности. Полезно прогнать один раз после настройки, не нужно оставлять постоянно работающим сервисом.

## Дальше

Сервер готов — переходите к [продакшн-запуску](production-run.md): клонирование репозитория, `just init prod <домен>`, `just run`, `just superuser`.
