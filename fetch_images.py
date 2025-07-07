import os
import re
import requests
import yaml
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from concurrent.futures import ThreadPoolExecutor
import threading
from itertools import count

CONFIG_FILE = 'config.yml'
RESOURCES_DIR = 'resources'
DECK_DIR = os.path.join(RESOURCES_DIR, 'deck')
CARD_LIST_FILE = 'card-list.txt'

_pair_counter = count(1)
_counter_lock = threading.Lock()


def _next_pair_id():
    with _counter_lock:
        return next(_pair_counter)


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def parse_card_list(path=CARD_LIST_FILE):
    """Parse a card list file.

    Accepted formats:
        ``1 Card Name``
        ``1 Card Name (SET)``
        ``1 Card Name (SET) 123``
        ``1 Card Name (SET) ABC-123``
    A trailing ``*F*`` flag is ignored, e.g. ``1 Card Name (SET) 123 *F*``.
    """

    cards = []
    if not os.path.exists(path):
        return cards

    line_re = re.compile(
        r"^(\d+)\s+(.*?)(?:\s+(?:\(([^)]+)\)|\[([^\]]+)\])(?:\s+([^\s]+))?)?(?:\s+\*F\*)?$",
        re.IGNORECASE,
    )

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = line_re.match(line)
            if not m:
                continue
            qty = int(m.group(1))
            name = m.group(2).strip()
            set_code = m.group(3) or m.group(4)
            collector = m.group(5)
            cards.append((qty, name, set_code, collector))
    return cards


def download_image(url, dest):
    resp = requests.get(url)
    resp.raise_for_status()
    with open(dest, 'wb') as f:
        f.write(resp.content)


INVALID_CHARS = r'[<>:"/\\|?*]'


def sanitize_filename(name: str) -> str:
    """Return *name* safe for filesystem storage."""
    clean = re.sub(INVALID_CHARS, '', name)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _append_lang(url: str, lang: str) -> str:
    """Return URL with `lang` query parameter added if missing."""
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    query.setdefault('lang', lang)
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))


def _fetch_single_card(qty, name, lang, set_code=None, collector=None):
    card_data = None

    if set_code and collector:
        url = f"https://api.scryfall.com/cards/{set_code}/{collector}/{lang}"
        r = requests.get(url)
        if r.status_code == 200:
            card_data = r.json()
    else:
        for language in (lang, 'en'):
            params = {'exact': name, 'lang': language}
            if set_code:
                params['set'] = set_code
            r = requests.get(
                'https://api.scryfall.com/cards/named',
                params=params,
            )
            if r.status_code == 200:
                card_data = r.json()
                break
        if not card_data:
            for language in (lang, 'en'):
                params = {'fuzzy': name, 'lang': language}
                if set_code:
                    params['set'] = set_code
                r = requests.get(
                    'https://api.scryfall.com/cards/named',
                    params=params,
                )
                if r.status_code == 200:
                    card_data = r.json()
                    break
    if not card_data:
        print(
            f"Advertencia: no se encontró la carta '{name}' en Scryfall. "
            "Por favor añádela manualmente."
        )
        return

    if card_data.get('lang') != lang:
        print(
            f"Advertencia: la carta '{name}' no está disponible en idioma "
            f"{lang}. Se descargará la versión en {card_data.get('lang')}."
        )

    if 'image_uris' in card_data:
        img_url = card_data['image_uris'].get('png') or card_data['image_uris'].get('large')
        img_url = _append_lang(img_url, lang)
        card_name = card_data.get('printed_name') or card_data['name']
        card_name = sanitize_filename(card_name)
        fname = f"{qty} {card_name}.png"
        path = os.path.join(DECK_DIR, fname)
        download_image(img_url, path)
    elif 'card_faces' in card_data and len(card_data['card_faces']) >= 2:
        front = card_data['card_faces'][0]
        back = card_data['card_faces'][1]
        for _ in range(qty):
            ident = f"{_next_pair_id():02d}"
            front_name = front.get('printed_name') or front['name']
            back_name = back.get('printed_name') or back['name']
            front_name = sanitize_filename(front_name)
            back_name = sanitize_filename(back_name)
            fpath = os.path.join(DECK_DIR, f"F{ident} {front_name}.png")
            bpath = os.path.join(DECK_DIR, f"B{ident} {back_name}.png")
            front_url = front['image_uris'].get('png') or front['image_uris'].get('large')
            back_url = back['image_uris'].get('png') or back['image_uris'].get('large')
            download_image(_append_lang(front_url, lang), fpath)
            download_image(_append_lang(back_url, lang), bpath)
    else:
        print(
            f"Advertencia: no se encontró imagen para la carta '{name}'. "
            "Por favor añádela manualmente."
        )


def fetch_images():
    cfg = load_config()
    lang = cfg.get('language-default', 'es')
    cards = parse_card_list()
    os.makedirs(DECK_DIR, exist_ok=True)
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_fetch_single_card, qty, name, lang, set_code, collector)
            for qty, name, set_code, collector in cards
        ]
        for f in futures:
            f.result()


if __name__ == '__main__':
    fetch_images()
