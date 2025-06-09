import os
import re
import math
import yaml
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.utils import ImageReader

CONFIG_FILE = 'config.yml'
DECK_DIR = 'deck-to-print'

CARD_PATTERN = re.compile(r'^(?:(\d+)\s+)?([FB]?)(\d{2})?\s+(.*)\.(?:jpg|png)$', re.IGNORECASE)

PAGE_SIZES = {
    'A4': A4,
    'LETTER': LETTER,
}

def mm_to_pt(mm: float) -> float:
    return mm * 72 / 25.4


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        cfg = yaml.safe_load(f)
    page_size = PAGE_SIZES.get(cfg.get('PAGE_SIZE', 'A4').upper(), A4)
    cfg['page_size'] = page_size
    cfg['margin_pt'] = mm_to_pt(cfg.get('MARGIN_MM', 0))
    cfg['gap_pt'] = mm_to_pt(cfg.get('GAP_MM', 0))
    return cfg


def parse_deck(config):
    cards = []
    backs = {}
    entries = []
    for fname in sorted(os.listdir(DECK_DIR)):
        match = CARD_PATTERN.match(fname)
        if not match:
            continue
        qty = int(match.group(1)) if match.group(1) else 1
        fb = match.group(2).upper() if match.group(2) else ''
        ident = match.group(3)
        name = match.group(4)
        path = os.path.join(DECK_DIR, fname)
        entries.append({'qty': qty, 'fb': fb, 'id': ident, 'name': name, 'path': path})

    for e in entries:
        if e['fb'] == 'B' and e['id']:
            backs[e['id']] = e['path']

    for e in entries:
        if e['fb'] == 'B':
            continue
        back = None
        if e['fb'] == 'F' and e['id'] and e['id'] in backs:
            back = backs[e['id']]
        if not back:
            back = config.get('DEFAULT_BACK')
        for _ in range(e['qty']):
            cards.append({'front': e['path'], 'back': back})
    return cards


def build_pages(cards, cols, rows):
    cards_per_page = cols * rows
    pages = []
    for i in range(0, len(cards), cards_per_page):
        pages.append(cards[i:i + cards_per_page])
    return pages


def draw_pages(pdf_path, pages, config, front=True):
    page_size = config['page_size']
    margin = config['margin_pt']
    gap = config['gap_pt']
    cols, rows = config['GRID']
    page_width, page_height = page_size
    cell_width = (page_width - 2 * margin - (cols - 1) * gap) / cols
    cell_height = (page_height - 2 * margin - (rows - 1) * gap) / rows

    c = canvas.Canvas(pdf_path, pagesize=page_size)
    for page in pages:
        for idx, card in enumerate(page):
            col = idx % cols
            row = idx // cols
            x = margin + col * (cell_width + gap)
            y = page_height - margin - (row + 1) * cell_height - row * gap
            img_path = card['front'] if front else card['back']
            img = Image.open(img_path)
            img_reader = ImageReader(img)
            c.drawImage(img_reader, x, y, width=cell_width, height=cell_height)
        c.showPage()
    c.save()


def main():
    config = load_config()
    cards = parse_deck(config)
    cols, rows = config['GRID']
    pages = build_pages(cards, cols, rows)
    draw_pages('fronts.pdf', pages, config, front=True)
    draw_pages('backs.pdf', pages, config, front=False)


if __name__ == '__main__':
    main()
