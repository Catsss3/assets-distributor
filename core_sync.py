import os
import base64
import logging
import re
import html
import socket
from typing import Set, List, Optional

import requests
from requests.adapters import HTTPAdapter, Retry
import google.generativeai as genai

# -------------------------------------------------
# Конфигурация (читаем именно те имена, которые заданы в Secrets)
# -------------------------------------------------
GITHUB_TOKEN = os.getenv("GITHAB_TOKEN")          # Твой секрет для GitHub
if not GITHUB_TOKEN:
    raise RuntimeError("Переменная окружения GITHAB_TOKEN не найдена")

GEMINI_KEY = os.getenv("GEMINI_API")              # Твой секрет для Gemini
# Если ключ не нужен – оставляем None, скрипт будет работать без AI‑расширения

REPO = "Catsss3/assets-distributor"
TARGET_FILE = "data_manifest.txt"
BRANCH = "main"

# -------------------------------------------------
# Источники vless‑ссылок
# -------------------------------------------------
GITHUB_SOURCES = [
    "https://github.com/Epodonios/v2ray-configs/raw/main/Splitted-By-Protocol/vless.txt",
    "https://github.com/mahdibland/V2RayAggregator/raw/master/sub/splitted/vless.txt",
    "https://raw.githubusercontent.com/fedeit/v2ray-configs/main/vless.txt",
]

TG_CHANNELS = ["mrsoulb", "config_fre", "v2ray_collector", "vless_config", "AchaVPN"]

# (опционально) whitelist‑домены для фильтрации или проверки
SNI_WHITELIST = {"travel.yandex.ru", "google.com", "microsoft.com"}

# -------------------------------------------------
# Логгер
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# -------------------------------------------------
# Инициализация Gemini (если ключ есть)
# -------------------------------------------------
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        logging.info("✅ Gemini инициализирован.")
    except Exception as e:
        logging.warning("Не удалось настроить Gemini: %s. AI‑расширение отключено.", e)
        GEMINI_KEY = None
else:
    logging.info("🔸 GEMINI_API не задан – AI‑расширение отключено.")

# -------------------------------------------------
# HTTP‑сессия с retry
# -------------------------------------------------
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "PUT"],
)
session.mount("https://", HTTPAdapter(max_retries=retries))

# -------------------------------------------------
# Вспомогательные функции
# -------------------------------------------------
def check_node(url: str) -> bool:
    """Проверка доступности host:port из ссылки."""
    try:
        match = re.search(r"@([^:]+):([0-9]+)", url)
        if not match:
            return False
        host, port = match.groups()
        with socket.create_connection((host, int(port)), timeout=1.5):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        logging.debug("Недоступен %s – %s", url, e)
        return False


def ai_enrich(text: str) -> List[str]:
    """Запрос к Gemini для извлечения vless‑ссылок из большого текста."""
    if not GEMINI_KEY:
        return []
    try:
        prompt = f"Extract only vless:// links from this text: {text[:4000]}"
        resp = model.generate_content(prompt)
        return re.findall(r"vless://[^\s\"'<>]+", resp.text, re.IGNORECASE)
    except Exception as e:
        logging.debug("Gemini‑error: %s", e)
        return []


def fetch_from_telegram() -> Set[str]:
    """Скачивает публичные каналы Telegram и собирает ссылки."""
    nodes: Set[str] = set()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AssetBot/3.1"}
    for ch in TG_CHANNELS:
        try:
            r = session.get(f"https://t.me/s/{ch}", headers=headers, timeout=10)
            r.raise_for_status()
            content = html.unescape(r.text)
            nodes.update(re.findall(r"vless://[^\s\"'<>]+", content, re.IGNORECASE))

            if GEMINI_KEY and len(content) > 1500:
                nodes.update(ai_enrich(content))
        except Exception as e:
            logging.debug("Ошибка TG‑канала %s: %s", ch, e)
    return nodes


def fetch_from_github_sources() -> Set[str]:
    """Скачивает файлы‑списки с GitHub и извлекает ссылки."""
    nodes: Set[str] = set()
    for src in GITHUB_SOURCES:
        try:
            r = session.get(src, timeout=10, headers={"User-Agent": "AssetBot/3.1"})
            r.raise_for_status()
            nodes.update(re.findall(r"vless://[^\s\"'<>]+", r.text, re.IGNORECASE))
        except Exception as e:
            logging.debug("Не удалось загрузить %s: %s", src, e)
    return nodes


def get_file_sha() -> Optional[str]:
    """Получает SHA текущей версии файла (если он существует)."""
    api_url = f"https://api.github.com/repos/{REPO}/contents/{TARGET_FILE}"
    resp = session.get(
        api_url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    if resp.status_code == 200:
        try:
            return resp.json()["sha"]
        except Exception as e:
            logging.error("Не удалось извлечь SHA: %s", e)
            return None
    if resp.status_code == 404:
        logging.info("Файл %s ещё не существует – будет создан.", TARGET_FILE)
        return None
    raise RuntimeError(f"Ошибка получения SHA: {resp.status_code} {resp.text}")


def commit_file(content: str, sha: Optional[str]) -> None:
    """Создаёт или обновляет файл в репозитории."""
    api_url = f"https://api.github.com/repos/{REPO}/contents/{TARGET_FILE}"
    payload = {
        "message": "Update asset manifest [skip ci]" if sha else "Initial asset manifest",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    resp = session.put(
        api_url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        },
        json=payload,
    )

    if resp.status_code in (200, 201):
        action = "обновлен" if sha else "создан"
        logging.info("✅ Файл %s успешно %s.", TARGET_FILE, action)
    else:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Ошибка PUT: {resp.status_code} {detail}")


# -------------------------------------------------
# Основная функция
# -------------------------------------------------
def main() -> None:
    nodes = fetch_from_telegram()
    nodes.update(fetch_from_github_sources())

    logging.info("📊 Собрано %d уникальных ссылок. Проверяем доступность...", len(nodes))

    live = [n for n in nodes if check_node(n)]

    if not live:
        logging.warning("📭 Живых узлов не найдено – ничего не коммитим.")
        return

    content = "\n".join(sorted(set(live))) + "\n"

    sha = get_file
