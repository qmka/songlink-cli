import argparse
import itertools
import json
import os
import re
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests
from colorama import Fore, Style
from colorama import init as colorama_init
from pyfiglet import Figlet

# ---------- Константы ----------
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ODESLI_LINKS_URL = "https://api.song.link/v1-alpha.1/links"

CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "songlink_cli"
CACHE_FILE = CACHE_DIR / "cache.json"

DELUXE_MARKERS = [
    "deluxe",
    "remaster",
    "remastered",
    "expanded",
    "anniversary",
    "special edition",
    "bonus track",
    "bonus tracks",
    "super deluxe",
    "tour edition",
    "collector",
    "redux",
]


# ---------- Утилиты ----------


def print_banner() -> None:
    colorama_init()
    fig = Figlet(font="slant", width=120)
    title = fig.renderText("SONGLINK")
    print(Style.BRIGHT + Fore.MAGENTA + title + Style.RESET_ALL)
    print(Fore.CYAN + "smart-link generator • iTunes → Odesli • just pageUrl" + Style.RESET_ALL)
    print()


def load_cache() -> dict[str, Any]:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return {}
    except Exception:
        return {}


def save_cache(cache: dict[str, Any]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def normalize(s: str) -> str:
    s = re.sub(r"[\[\](){}]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().casefold()


def strip_edition_tags(title: str) -> tuple[str, bool]:
    base = re.sub(
        r"\s*[-–—]\s*(deluxe|remaster.*|expanded|anniversary|special edition|bonus tracks?).*$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    base = re.sub(
        r"\s*\((deluxe|remaster.*|expanded|anniversary|special edition|bonus tracks?)\)\s*$",
        "",
        base,
        flags=re.IGNORECASE,
    )
    changed = base != title
    return base, changed


def has_deluxe_marker(title: str) -> bool:
    n = normalize(title)
    return any(m in n for m in DELUXE_MARKERS)


def load_template(template_path: Optional[str]) -> Optional[str]:
    """Загружаем шаблон. Приоритет: --template → рядом со скриптом template.txt"""
    # 1. Явный путь
    if template_path:
        p = Path(template_path)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None

    # 2. template.txt рядом со скриптом
    script_dir = Path(__file__).resolve().parent
    script_tpl = script_dir / "template.txt"
    if script_tpl.exists():
        return script_tpl.read_text(encoding="utf-8")

    return None


def render_template(
    tpl: str, *, url: str, artist: Optional[str], album: Optional[str], query: Optional[str]
) -> str:
    data = {
        "url": url,
        "artist": artist or "",
        "album": album or "",
        "query": query or "",
    }

    class SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    return tpl.format_map(SafeDict(data))


@dataclass
class ITunesAlbum:
    collectionName: str
    artistName: str
    collectionViewUrl: str
    releaseDate: Optional[str] = None
    collectionId: Optional[int] = None


def search_itunes(
    artist: Optional[str], album: Optional[str], query: Optional[str], limit: int = 5
) -> list[ITunesAlbum]:
    term = query or f"{artist} {album}".strip()
    params = {
        "term": term,
        "entity": "album",
        "limit": str(limit),
        "media": "music",
    }
    resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for r in data.get("results", []):
        if r.get("wrapperType") != "collection":
            continue
        items.append(
            ITunesAlbum(
                collectionName=r.get("collectionName", ""),
                artistName=r.get("artistName", ""),
                collectionViewUrl=r.get("collectionViewUrl", ""),
                releaseDate=r.get("releaseDate"),
                collectionId=r.get("collectionId"),
            )
        )
    return items


def score_candidate(c: ITunesAlbum, artist_in: Optional[str], album_in: Optional[str]) -> float:
    title_norm = normalize(c.collectionName)
    artist_norm = normalize(c.artistName)
    base_title_norm = normalize(album_in or "")
    base_artist_norm = normalize(artist_in or "")

    score = 0.0
    if base_artist_norm and base_artist_norm == artist_norm:
        score += 50
    elif base_artist_norm and base_artist_norm in artist_norm:
        score += 25
    if base_title_norm and base_title_norm == title_norm:
        score += 50
    elif base_title_norm and base_title_norm in title_norm:
        score += 25
    if has_deluxe_marker(c.collectionName):
        score -= 10
    stripped, changed = strip_edition_tags(c.collectionName)
    if changed and normalize(stripped) == base_title_norm:
        score += 10
    return score


def choose_candidate(
    cands: list[ITunesAlbum], artist: Optional[str], album: Optional[str], non_interactive: bool
) -> Optional[ITunesAlbum]:
    if not cands:
        return None
    cands_scored = sorted(cands, key=lambda c: score_candidate(c, artist, album), reverse=True)
    return cands_scored[0] if non_interactive or len(cands_scored) == 1 else cands_scored[0]


def odesli_page_url(source_url: str) -> Optional[str]:
    params = {"url": source_url}
    delay = 0.8
    for _attempt in range(5):
        resp = requests.get(ODESLI_LINKS_URL, params=params, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("pageUrl")
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(delay)
            delay *= 1.8
            continue
        resp.raise_for_status()
    return None


def cache_key(artist: Optional[str], album: Optional[str], query: Optional[str]) -> str:
    payload = {
        "artist": artist or "",
        "album": album or "",
        "query": query or "",
        "v": 1,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def maybe_copy_to_clipboard(s: str, do_copy: bool) -> None:
    if not do_copy:
        return
    try:
        import pyperclip

        pyperclip.copy(s)
        print("🔗 Скопировано в буфер обмена.")
    except Exception as e:
        print(f"⚠️ Не удалось скопировать в буфер обмена: {e}")


# ---------- Main ----------


def spinner(stop_event):
    for c in itertools.cycle(["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]):
        if stop_event.is_set():
            break
        sys.stdout.write(Fore.YELLOW + f"\r🔍 Ищем ссылку... {c}" + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r")  # очистка строки


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", type=str)
    parser.add_argument("--album", type=str)
    parser.add_argument("--query", type=str)
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--copy", action="store_true")
    parser.add_argument("--no-banner", action="store_true")
    parser.add_argument("--template", type=str)
    parser.add_argument("--use-template", action="store_true")
    parser.add_argument("--copy-template", action="store_true")
    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    if not args.query and not (args.artist and args.album):
        print("Нужно указать --query 'Artist — Album' или оба параметра.", file=sys.stderr)
        sys.exit(2)

    start_time = time.time()

    # запускаем спиннер
    stop_event = threading.Event()
    t = threading.Thread(target=spinner, args=(stop_event,))
    t.start()

    cache = load_cache()
    key = cache_key(args.artist, args.album, args.query)
    if key in cache:
        page = cache[key]
    else:
        candidates = search_itunes(args.artist, args.album, args.query, limit=5)
        if not candidates:
            stop_event.set()
            t.join()
            print(Fore.RED + "❌ Ничего не нашлось в iTunes." + Style.RESET_ALL, file=sys.stderr)
            sys.exit(1)
        chosen = choose_candidate(candidates, args.artist, args.album, args.non_interactive)
        if not chosen:
            stop_event.set()
            t.join()
            print(Fore.RED + "❌ Не удалось выбрать альбом." + Style.RESET_ALL, file=sys.stderr)
            sys.exit(1)
        page = odesli_page_url(chosen.collectionViewUrl)
        if not page:
            stop_event.set()
            t.join()
            print(Fore.RED + "❌ Альбом не найден на Odesli." + Style.RESET_ALL, file=sys.stderr)
            sys.exit(1)
        cache[key] = page
        save_cache(cache)

    # останавливаем спиннер
    stop_event.set()
    t.join()

    # --- шаблон ---
    tpl = None
    formatted = None
    if args.use_template or args.copy_template:
        tpl = load_template(args.template)
        if tpl:
            formatted = render_template(
                tpl,
                url=page,
                artist=args.artist,
                album=args.album,
                query=args.query,
            )
        else:
            print("⚠️ Шаблон не найден. Выведу голую ссылку.", file=sys.stderr)

    # показать какой запрос найден
    if args.query:
        found_label = args.query
    else:
        found_label = f"{args.artist} — {args.album}"
    elapsed = time.time() - start_time
    print(Fore.GREEN + f"✅ Найдено: {found_label}" + Style.RESET_ALL)
    print(Fore.CYAN + f"⏱ Время выполнения: {elapsed:.2f} сек." + Style.RESET_ALL)

    # печать результата
    if args.use_template and formatted:
        print(formatted)
    else:
        print(page)

    # копирование
    if args.copy_template and formatted:
        maybe_copy_to_clipboard(formatted, True)
    elif args.copy:
        maybe_copy_to_clipboard(page, True)

    # открыть в браузере
    if args.open:
        webbrowser.open(page)


if __name__ == "__main__":
    main()
