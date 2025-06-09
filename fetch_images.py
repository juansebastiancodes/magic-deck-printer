import os
import re
import requests
import yaml

CONFIG_FILE = 'config.yml'
RESOURCES_DIR = 'resources'
DECK_DIR = os.path.join(RESOURCES_DIR, 'deck')
CARD_LIST_FILE = 'card-list.txt'


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def parse_card_list(path=CARD_LIST_FILE):
    cards = []
    if not os.path.exists(path):
        return cards
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'^(\d+)\s+(.+)$', line)
            if not m:
                continue
            qty = int(m.group(1))
            name = m.group(2)
            cards.append((qty, name))
    return cards


def download_image(url, dest):
    resp = requests.get(url)
    resp.raise_for_status()
    with open(dest, 'wb') as f:
        f.write(resp.content)


def fetch_images():
    cfg = load_config()
    lang = cfg.get('language-default', 'es')
    cards = parse_card_list()
    os.makedirs(DECK_DIR, exist_ok=True)
    pair_id = 1
    for qty, name in cards:
        card_data = None
        for language in (lang, 'en'):
            r = requests.get(
                'https://api.scryfall.com/cards/named',
                params={'exact': name, 'lang': language},
            )
            if r.status_code == 200:
                card_data = r.json()
                break
        if not card_data:
            print(f'Card not found: {name}')
            continue

        if 'image_uris' in card_data:
            img_url = card_data['image_uris'].get('png') or card_data['image_uris'].get('large')
            fname = f"{qty} {card_data['name']}.png"
            path = os.path.join(DECK_DIR, fname)
            download_image(img_url, path)
        elif 'card_faces' in card_data and len(card_data['card_faces']) >= 2:
            front = card_data['card_faces'][0]
            back = card_data['card_faces'][1]
            for _ in range(qty):
                ident = f"{pair_id:02d}"
                fpath = os.path.join(DECK_DIR, f"F{ident} {front['name']}.png")
                bpath = os.path.join(DECK_DIR, f"B{ident} {back['name']}.png")
                download_image(front['image_uris'].get('png') or front['image_uris'].get('large'), fpath)
                download_image(back['image_uris'].get('png') or back['image_uris'].get('large'), bpath)
                pair_id += 1
        else:
            print(f'No images for card: {name}')


if __name__ == '__main__':
    fetch_images()
