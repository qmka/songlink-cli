# 🎵 songlink-cli

Консольная утилита на Python для быстрого получения **умной ссылки [Odesli](https://odesli.co/) (Songlink)**  
по названию артиста и альбома.

Odesli генерирует красивую веб-страницу для альбома, где слушатель сам выбирает сервис, где хочет слушать музыку. Представленная утилита вытягивает из Odesli ссылку на эту самую страницу (например, для вставки её в блоге/форуме).  


---

## ✨ Возможности

- 🔗 Получение `pageUrl` (умной ссылки Odesli) по артисту и альбому
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
   git clone https://github.com/qmka/songlink-cli.git
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
uv run -m songlink_cli --artist "Calva Louise" --album "Edge of the Abyss"

# Поиск одной строкой
uv run -m songlink_cli --query "Calva Louise — Edge of the Abyss"

# Скопировать ссылку в буфер обмена
uv run -m songlink_cli --query "Calva Louise — Edge of the Abyss" --copy

# Открыть результат сразу в браузере
uv run -m songlink_cli --query "Calva Louise — Edge of the Abyss" --open

# Использовать шаблон из template.txt рядом со скриптом
uv run -m songlink_cli --query "Calva Louise — Edge of the Abyss" --use-template

# Вывести по шаблону и скопировать в буфер
uv run -m songlink_cli --query "Calva Louise — Edge of the Abyss" --use-template --copy-template
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

## 📦 Установка как пакета

Проект можно поставить в систему так, чтобы он запускался по имени `songlink` прямо из консоли.

### 1. Клонируй репозиторий
```bash
git clone https://github.com/qmka/songlink-cli.git
cd songlink-cli
```

### 2. Установи пакет в режиме разработки
Если используешь [uv](https://github.com/astral-sh/uv):
```bash
uv pip install -e .
```

или через обычный pip:
```bash
pip install -e .
```

### 3. Запускай утилиту из консоли
Теперь доступна команда:
```bash
songlink --query "Calva Louise — Edge of the Abyss"
```

Флаги и параметры такие же, как при запуске через `uv run -m songlink_cli`.

---

## ⚡ Текущие ограничения

- Используется только iTunes Search API → обычно выдаёт US-релиз по умолчанию  
- Если альбом не найден в Odesli, утилита честно напишет ❌ и завершится  
- Для региональных рынков (RU, DE и т. д.) нет отдельной поддержки (но не факт, что она нужна)  

---

## 📜 Лицензия

MIT — используй, форкай, дорабатывай 🔥
