import os
from datetime import datetime
from reportlab.pdfgen import canvas
from generate_pdf import load_config, RESULTS_DIR, _draw_crosses


def _single_page(c, config, front):
    page_width, page_height = config['page_size']
    angle = float(config.get('page_rotation_deg', 0)) if not front else 0
    if angle < 0:
        angle = 360 - angle
    c.saveState()
    c.translate(page_width/2, page_height/2)
    if angle:
        c.rotate(angle)
    c.translate(-page_width/2, -page_height/2)
    x_off = config.get('back_offset_pt', 0) if not front else 0
    y_off = config.get('vertical_back_offset_pt', 0) if not front else 0
    cfg = dict(config)
    cfg['_force_cross'] = True
    _draw_crosses(c, cfg, front, x_off, y_off)
    c.restoreState()


def draw_calibration(pdf_path, config):
    c = canvas.Canvas(pdf_path, pagesize=config['page_size'])
    _single_page(c, config, True)
    c.showPage()
    _single_page(c, config, False)
    c.showPage()
    c.save()


if __name__ == '__main__':
    cfg = load_config()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_path = os.path.join(RESULTS_DIR, f'calibration_{timestamp}.pdf')
    draw_calibration(pdf_path, cfg)
