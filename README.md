# 🎵 songlink-cli

Консольная утилита на Python для быстрого получения **умной ссылки Odesli (Songlink)**  
по названию артиста и альбома.  

Ссылка открывается в красивой веб-странице, где слушатель сам выбирает сервис  
(Spotify, Apple Music, Deezer, YouTube Music и т. д.).

---

## ✨ Возможности

- 🔗 Получение `pageUrl` (умной ссылки Odesli) по артисту и альбому  
- 🎨 Красивый баннер при запуске  
- 💾 Кэширование результатов (повторные запросы мгновенные)  
- 📋 Копирование результата в буфер обмена (`--copy`)  
- 📑 Поддержка шаблонов: можно задать свой `template.txt`, где будут плейсхолдеры:
  - `{url}` — итоговая ссылка Odesli  
  - `{artist}` — артист  
  - `{album}` — альбом  
  - `{query}` — вся строка запроса  
- 🖼 Форматировать вывод по шаблону (`--use-template`) или сразу скопировать в буфер (`--copy-template`)  
- 🌍 Работает без регистрации, токенов и ключей (используется iTunes Search API и Odesli API)  

---

## 🚀 Установка и запуск

1. Клонируй репозиторий и перейди в директорию проекта:
   ```bash
   git clone https://github.com/username/songlink-cli.git
   cd songlink-cli
   ```

2. Установи зависимости через [uv](https://github.com/astral-sh/uv):
   ```bash
   uv sync
   ```

3. Запуск утилиты:
   ```bash
   uv run -m songlink_cli --artist "Halestorm" --album "Everest"
   ```

---

## 🛠 Примеры использования

```bash
# Поиск по артисту и альбому
uv run -m songlink_cli --artist "Halestorm" --album "Everest"

# Поиск одной строкой
uv run -m songlink_cli --query "Svartsot — Peregrinus"

# Скопировать ссылку в буфер обмена
uv run -m songlink_cli --query "Svartsot — Peregrinus" --copy

# Открыть результат сразу в браузере
uv run -m songlink_cli --query "Svartsot — Peregrinus" --open

# Использовать шаблон из template.txt рядом со скриптом
uv run -m songlink_cli --query "Svartsot — Peregrinus" --use-template

# Вывести по шаблону и скопировать в буфер
uv run -m songlink_cli --query "Svartsot — Peregrinus" --use-template --copy-template
```

---

## 📑 Пример template.txt

Файл `template.txt` должен лежать рядом с `songlink_cli.py`.  
Внутри можно использовать плейсхолдеры `{url}`, `{artist}`, `{album}`, `{query}`.

### Markdown:
```text
🎵 {artist} — {album}  
[Послушать]({url})
```

### HTML:
```html
<p>🎵 <strong>{artist} — {album}</strong><br>
<a href="{url}">Послушать</a></p>
```

### BBCode:
```text
[b]{artist} — {album}[/b]
[url={url}]Послушать[/url]
```

---

## ⚡ Текущие ограничения

- Используется только iTunes Search API → иногда выдаёт US-релиз по умолчанию  
- Если альбом не найден в Odesli, утилита честно напишет ❌ и завершится  
- Для специфических рынков (RU, DE и т. д.) пока нет отдельной поддержки  

---

## 📜 Лицензия

MIT — используй, форкай, дорабатывай 🔥
