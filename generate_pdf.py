import os
import re
import math
import yaml
from datetime import datetime
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.utils import ImageReader

CONFIG_FILE = 'config.yml'
RESOURCES_DIR = 'resources'
DECK_DIR = os.path.join(RESOURCES_DIR, 'deck')
RESULTS_DIR = 'results'

CARD_PATTERN = re.compile(
    r'^(?:(\d+)\s+)?(?:([FB])(\d{2})\s+)?(.*)\.(?:jpg|png)$',
    re.IGNORECASE,
)

PAGE_SIZES = {
    'A4': A4,
    'LETTER': LETTER,
}

CARD_WIDTH_MM = 63.5  # 2.5 inches
CARD_HEIGHT_MM = 88.9  # 3.5 inches

def mm_to_pt(mm: float) -> float:
    return mm * 72 / 25.4


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        cfg = yaml.safe_load(f)
    page_size = PAGE_SIZES.get(cfg.get('PAGE_SIZE', 'A4').upper(), A4)
    cfg['page_size'] = page_size
    cfg['margin_pt'] = mm_to_pt(cfg.get('MARGIN_MM', 0))
    cfg['gap_pt'] = mm_to_pt(cfg.get('GAP_MM', 0))
    cfg['card_width_pt'] = mm_to_pt(CARD_WIDTH_MM)
    cfg['card_height_pt'] = mm_to_pt(CARD_HEIGHT_MM)
    cfg.setdefault('pages-intercalation', True)
    cfg['back_offset_pt'] = mm_to_pt(cfg.get('horizontal-back-offset', -2))
    cfg['vertical_back_offset_pt'] = mm_to_pt(cfg.get('vertical-back-offset', 0))
    cfg['back_oversize_pt'] = mm_to_pt(cfg.get('back-oversize', 0.2))
    cfg['page_rotation_deg'] = cfg.get('page-rotation-degrees', 0)
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


def compute_grid(config):
    page_width, page_height = config['page_size']
    margin = config['margin_pt']
    gap = config['gap_pt']
    card_w = config['card_width_pt']
    card_h = config['card_height_pt']

    cols = max(1, int((page_width - 2 * margin + gap) // (card_w + gap)))
    rows = max(1, int((page_height - 2 * margin + gap) // (card_h + gap)))
    return cols, rows


def _draw_single_page(canvas_obj, page, config, front):
    page_size = config['page_size']
    margin = config['margin_pt']
    gap = config['gap_pt']
    cols, rows = config['GRID']
    page_width, page_height = page_size
    cell_width = config['card_width_pt']
    cell_height = config['card_height_pt']
    angle = float(config.get('page_rotation_deg', 0)) if not front else 0

    # ReportLab rotates counter-clockwise for positive values.  The
    # configuration may include negative numbers for clockwise rotation.
    # ``rotate`` does not accept negative values, so for negative angles we
    # convert them using ``360 - angle`` to preserve the desired orientation
    # while keeping the argument positive.  Positive values are used as-is.
    if angle < 0:
        angle = 360 - angle

    canvas_obj.saveState()
    canvas_obj.translate(page_width/2, page_height/2)
    if angle:
        canvas_obj.rotate(angle)
    canvas_obj.translate(-page_width/2, -page_height/2)

    oversize = config.get('back_oversize_pt', 0) if not front else 0

    extra_x = page_width - 2 * margin - cols * cell_width - (cols - 1) * gap
    extra_x = max(0, extra_x)
    right_margin = margin + extra_x

    for idx, card in enumerate(page):
        col = idx % cols
        row = idx // cols
        if front:
            x = margin + col * (cell_width + gap)
        else:
            x = right_margin + (cols - 1 - col) * (cell_width + gap) + config.get('back_offset_pt', 0)
        x -= oversize / 2
        y = page_height - margin - cell_height - row * (cell_height + gap)
        if not front:
            y += config.get('vertical_back_offset_pt', 0)
        y -= oversize / 2
        img_path = card['front'] if front else card['back']
        img = Image.open(img_path)
        img_reader = ImageReader(img)
        if front:
            width = cell_width
            height = cell_height
        else:
            width = cell_width + oversize
            height = cell_height + oversize
        canvas_obj.drawImage(img_reader, x, y, width=width, height=height)

    canvas_obj.restoreState()


def draw_pages(pdf_path, pages, config, front=True):
    c = canvas.Canvas(pdf_path, pagesize=config['page_size'])
    for page in pages:
        _draw_single_page(c, page, config, front)
        c.showPage()
    c.save()


def draw_pages_intercalated(pdf_path, pages, config):
    c = canvas.Canvas(pdf_path, pagesize=config['page_size'])
    for page in pages:
        _draw_single_page(c, page, config, front=True)
        c.showPage()
        _draw_single_page(c, page, config, front=False)
        c.showPage()
    c.save()


def main():
    config = load_config()
    config['GRID'] = compute_grid(config)
    cards = parse_deck(config)
    cols, rows = config['GRID']
    pages = build_pages(cards, cols, rows)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if config.get('pages-intercalation', True):
        pdf_path = os.path.join(RESULTS_DIR, f'deck_{timestamp}.pdf')
        draw_pages_intercalated(pdf_path, pages, config)
    else:
        fronts_pdf = os.path.join(RESULTS_DIR, f'deck_{timestamp}_fronts.pdf')
        backs_pdf = os.path.join(RESULTS_DIR, f'deck_{timestamp}_backs.pdf')
        draw_pages(fronts_pdf, pages, config, front=True)
        draw_pages(backs_pdf, pages, config, front=False)


if __name__ == '__main__':
    main()
