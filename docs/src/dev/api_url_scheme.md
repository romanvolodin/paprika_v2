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

- Пагинация, фильтрация (`?assigned_to=me`, `?status=`), дефолтная сортировка — пока не решено, нужно продумать отдельно для каждого адреса.

## Загрузка файлов

- Не решено: отдельный адрес для вложений (`POST /shots/<id>/chat/<id>/attachments/`) или `multipart/form-data` прямо в теле создания сообщения/аватарки.

## WebSocket-адреса

- Префикс `/ws/v1/`; конкретные пути пока не определены.

## Формат ошибок и статус-коды

- Не решено: единый формат тела ошибки (`{"detail": ...}` vs `{"errors": [...]}`), 404 vs 403 для чужого проекта.
