# Схема адресов REST API

## Общие принципы

- Префикс `/api/v1/` для всех адресов.
- Множественное число, kebab-case для составных имён ресурсов (`shot-groups`, `shot-tasks`, `task-types`).
- Все адреса заканчиваются косой чертой.
- **Гибридная схема**:
  - list/create — через родителя.
  - retrieve/update/delete — прямой адрес по собственному id ресурса.

## Дерево адресов

Будет дополняться.

```txt
# Company
GET/POST         /api/v1/companies/
GET/PATCH/DELETE /api/v1/companies/<id>/

# TaskType
GET/POST         /api/v1/companies/<id>/task-types/
GET/PATCH/DELETE /api/v1/task-types/<id>/

# Project принадлежит компании
GET/POST         /api/v1/companies/<id>/projects/
GET/PATCH/DELETE /api/v1/projects/<id>/

# ShotGroup принадлежит проекту
GET/POST         /api/v1/projects/<id>/shot-groups/
GET/PATCH/DELETE /api/v1/shot-groups/<id>/

# Shot принадлежит группе
GET/POST         /api/v1/shot-groups/<id>/shots/
# Список кадров проекта
GET              /api/v1/projects/<id>/shots/
GET/PATCH/DELETE /api/v1/shots/<id>/

# ShotTask принадлежит кадру
GET/POST         /api/v1/shots/<id>/tasks/
GET/PATCH/DELETE /api/v1/shot-tasks/<id>/

# Version принадлежит кадру
GET/POST         /api/v1/shots/<id>/versions/
GET/PATCH/DELETE /api/v1/versions/<id>/

# Chat принадлежит кадру
GET/POST         /api/v1/shots/<id>/chat/
GET/PATCH/DELETE /api/v1/chat/<id>/

# Feed только собирает и отдает события за последнее время,
# адреса для создания нет
GET              /api/v1/projects/<id>/feed/
```

## Query-параметры списков

Базовые параметры:

- `page` — начинается с 1.
- `page_size` — по умолчанию 20, максимум 100.
- `search` — icontains по паре текстовых полей.

Ответ в виде `{items, total, page, page_size}`.

Новые списки используют этот паттерн, если нет причины отклониться.

Отклонения по ресурсам:

- **Shots** — дополнительный фильтр `assigned_to=<user_id>` (или `assigned_to=me`). Фильтрует по кадрам, у которых есть ShotTask, назначенный на пользователя.
- **Versions** — только базовые.
- **Chat** — курсорная пагинация вместо `page/page_size`: `limit` (по умолчанию 50), `before=<message_id>` для подгрузки более старых сообщений. Первый запрос без `before` — последние `limit` сообщений в хронологическом порядке.
- **TaskType** — без пагинации, отдается список целиком (опционально `search`).
- **Feed** — на данный момент собирает события из таблиц chat/task/version (отдельная таблица лога появится в будущем). По умолчанию отдаются события за последние 3 дня, подгрузка по датам (`before_date=`), а не по id — так как источник смешанный (три таблицы с разными id), а окно уже задаётся датой.

  Фильтры:
  - `type=chat,task,version`
  - `mine=true` — только события по кадрам, назначенным на пользователя
  - `created_by=<id>,<id>`
  - `date_from=`
  - `date_to=`

## Загрузка файлов

Способ загрузки файлов зависит от того, один файл у ресурса или много:

- **Один файл на ресурс** (аватар пользователя, обложка проекта) — загружается через `multipart/form-data` прямо в теле `POST`/`PATCH` создания/обновления самого ресурса, вместе с остальными полями.
- **Ресурс связан со множеством файлов** (вложения в чат, версии) — отдельный адрес загрузки, не связанный с ещё не существующим родителем. На примере чата:

  ```txt
  POST /shots/<id>/chat/attachments/   → {id, url, filename, size, content_type}
  POST /shots/<id>/chat/               → {text, attachment_ids: [1, 2]}
  ```

  Сначала грузим файлы и получаем их id, потом создаём сообщение со списком id. Это даёт прогресс и перезапуск загрузки (при необходимости) по каждому файлу отдельно, позволяет убрать файл до отправки и не плодит проблему "осиротевших" файлов за счёт того, что вложение — самостоятельный ресурс со своим id независимо от того, прикреплено ли оно уже к чему-то.

## WebSocket-адреса

- Префикс `/ws/v1/`; конкретные пути пока не определены.

## Формат ошибок и статус-коды

- Не решено: единый формат тела ошибки (`{"detail": ...}` vs `{"errors": [...]}`), 404 vs 403 для чужого проекта.
