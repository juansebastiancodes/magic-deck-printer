import importlib
import sys
import types
import pytest


def stub_dependencies(monkeypatch):
    # Create minimal PIL module
    pil = types.ModuleType('PIL')
    pil.Image = types.SimpleNamespace(open=lambda p: p)
    monkeypatch.setitem(sys.modules, 'PIL', pil)

    # Stub yaml module
    yaml_mod = types.ModuleType('yaml')
    yaml_mod.safe_load = lambda s: {}
    monkeypatch.setitem(sys.modules, 'yaml', yaml_mod)

    # Create minimal reportlab modules
    rl = types.ModuleType('reportlab')
    rl.pdfgen = types.ModuleType('pdfgen')

    class DummyCanvas:
        def __init__(self, *args, **kwargs):
            pass
        def drawImage(self, *args, **kwargs):
            pass
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass
        def rect(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    rl.pdfgen.canvas = types.SimpleNamespace(Canvas=DummyCanvas)
    rl.lib = types.ModuleType('lib')
    rl.lib.pagesizes = types.SimpleNamespace(A4=(1, 1), LETTER=(1, 1))
    rl.lib.utils = types.ModuleType('utils')
    rl.lib.utils.ImageReader = lambda img: img

    monkeypatch.setitem(sys.modules, 'reportlab', rl)
    monkeypatch.setitem(sys.modules, 'reportlab.pdfgen', rl.pdfgen)
    monkeypatch.setitem(sys.modules, 'reportlab.pdfgen.canvas', rl.pdfgen.canvas)
    monkeypatch.setitem(sys.modules, 'reportlab.lib', rl.lib)
    monkeypatch.setitem(sys.modules, 'reportlab.lib.pagesizes', rl.lib.pagesizes)
    monkeypatch.setitem(sys.modules, 'reportlab.lib.utils', rl.lib.utils)


@pytest.fixture
def gp(monkeypatch):
    stub_dependencies(monkeypatch)
    if 'generate_pdf' in sys.modules:
        del sys.modules['generate_pdf']
    return importlib.import_module('generate_pdf')


def test_mm_to_pt(gp):
    assert gp.mm_to_pt(25.4) == pytest.approx(72)


def test_build_pages(gp):
    cards = [{'front': 'f', 'back': 'b'} for _ in range(12)]
    pages = gp.build_pages(cards, 2, 5)
    assert len(pages) == 2
    assert len(pages[0]) == 10
    assert len(pages[1]) == 2


def test_parse_deck(monkeypatch, gp, tmp_path):
    deck = tmp_path / 'deck'
    deck.mkdir()
    # Sample images (can be empty files)
    (deck / 'F01 Card Front.jpg').write_text('')
    (deck / 'B01 Card Back.jpg').write_text('')
    (deck / '2 Swamp.jpg').write_text('')
    default_back = tmp_path / 'back.jpg'
    default_back.write_text('')

    monkeypatch.setattr(gp, 'DECK_DIR', str(deck))

    config = {'DEFAULT_BACK': str(default_back)}
    cards = gp.parse_deck(config)

    assert len(cards) == 3
    fronts = [c for c in cards if 'F01 Card Front.jpg' in c['front']]
    swamps = [c for c in cards if 'Swamp.jpg' in c['front']]
    assert len(fronts) == 1
    assert len(swamps) == 2
    assert fronts[0]['back'].endswith('B01 Card Back.jpg')
    assert all(c['back'] == str(default_back) for c in swamps)


def test_parse_deck_blank_back(monkeypatch, gp, tmp_path):
    deck = tmp_path / 'deck'
    deck.mkdir()
    (deck / '1 Plains.jpg').write_text('')

    monkeypatch.setattr(gp, 'DECK_DIR', str(deck))

    config = {'blank-back': True}
    cards = gp.parse_deck(config)

    assert len(cards) == 1
    assert cards[0]['back'] is None


def test_draw_pages_back_mirrored(monkeypatch, gp):
    positions = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, img, x, y, width=None, height=None):
            positions.append((x, y))
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (34, 100),  # extra space on the right
        'margin_pt': 5,
        'gap_pt': 0,
        'card_width_pt': 10,
        'card_height_pt': 20,
        'GRID': (2, 1),
    }
    pages = [[{'front': 'f1', 'back': 'b1'}, {'front': 'f2', 'back': 'b2'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert [p[0] for p in positions] == [17, 7]


def test_draw_pages_back_offset(monkeypatch, gp):
    positions = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, img, x, y, width=None, height=None):
            positions.append((x, y))
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (34, 100),
        'margin_pt': 5,
        'gap_pt': 0,
        'card_width_pt': 10,
        'card_height_pt': 20,
        'GRID': (2, 1),
        'back_offset_pt': 3,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}, {'front': 'f2', 'back': 'b2'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert [p[0] for p in positions] == [20, 10]


def test_draw_pages_vertical_back_offset(monkeypatch, gp):
    positions = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, img, x, y, width=None, height=None):
            positions.append((x, y))
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (34, 100),
        'margin_pt': 5,
        'gap_pt': 0,
        'card_width_pt': 10,
        'card_height_pt': 20,
        'GRID': (1, 2),
        'vertical_back_offset_pt': 4,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}, {'front': 'f2', 'back': 'b2'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert [p[1] for p in positions] == [54, 34]


def test_draw_pages_back_oversize(monkeypatch, gp):
    sizes = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, img, x, y, width=None, height=None):
            sizes.append((width, height))
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (34, 100),
        'margin_pt': 5,
        'gap_pt': 0,
        'card_width_pt': 10,
        'card_height_pt': 20,
        'GRID': (1, 1),
        'back_oversize_pt': 4,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert sizes[0] == (14, 24)


def test_draw_pages_front_no_oversize(monkeypatch, gp):
    sizes = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, img, x, y, width=None, height=None):
            sizes.append((width, height))
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (34, 100),
        'margin_pt': 5,
        'gap_pt': 0,
        'card_width_pt': 10,
        'card_height_pt': 20,
        'GRID': (1, 1),
        'back_oversize_pt': 4,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=True)

    assert sizes[0] == (10, 20)


def test_draw_blank_back(monkeypatch, gp):
    events = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, *a, **k):
            events.append('image')
        def rect(self, *a, **k):
            events.append('rect')
        def showPage(self):
            pass
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def setFillColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (34, 100),
        'margin_pt': 5,
        'gap_pt': 0,
        'card_width_pt': 10,
        'card_height_pt': 20,
        'GRID': (1, 1),
    }
    pages = [[{'front': 'f1', 'back': None}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert 'rect' in events
    assert 'image' not in events


def test_draw_pages_intercalated_order(monkeypatch, gp):
    events = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, img, x, y, width=None, height=None):
            events.append(img)
        def showPage(self):
            events.append('page')
        def saveState(self):
            pass
        def translate(self, *args, **kwargs):
            pass
        def rotate(self, *args, **kwargs):
            pass
        def restoreState(self):
            pass
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (10, 10),
        'margin_pt': 0,
        'gap_pt': 0,
        'card_width_pt': 1,
        'card_height_pt': 1,
        'GRID': (1, 1),
    }
    pages = [[{'front': 'f1', 'back': 'b1'}]]

    gp.draw_pages_intercalated('dummy.pdf', pages, cfg)

    assert events == ['f1', 'page', 'b1', 'page']


def test_page_rotation(monkeypatch, gp):
    calls = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, *a, **k):
            pass
        def showPage(self):
            pass
        def saveState(self):
            calls.append('saveState')
        def translate(self, x, y):
            calls.append(('translate', x, y))
        def rotate(self, angle):
            calls.append(('rotate', angle))
        def restoreState(self):
            calls.append('restoreState')
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (10, 10),
        'margin_pt': 0,
        'gap_pt': 0,
        'card_width_pt': 1,
        'card_height_pt': 1,
        'GRID': (1, 1),
        'page_rotation_deg': 45,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert ('rotate', 45.0) in calls


def test_page_rotation_negative(monkeypatch, gp):
    calls = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, *a, **k):
            pass
        def showPage(self):
            pass
        def saveState(self):
            calls.append('saveState')
        def translate(self, x, y):
            calls.append(('translate', x, y))
        def rotate(self, angle):
            calls.append(('rotate', angle))
        def restoreState(self):
            calls.append('restoreState')
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (10, 10),
        'margin_pt': 0,
        'gap_pt': 0,
        'card_width_pt': 1,
        'card_height_pt': 1,
        'GRID': (1, 1),
        'page_rotation_deg': -30,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=False)

    assert ('rotate', 390.0) in calls


def test_page_rotation_front_unchanged(monkeypatch, gp):
    calls = []

    class RecCanvas:
        def __init__(self, *a, **k):
            pass
        def drawImage(self, *a, **k):
            pass
        def showPage(self):
            pass
        def saveState(self):
            calls.append('saveState')
        def translate(self, x, y):
            calls.append(('translate', x, y))
        def rotate(self, angle):
            calls.append(('rotate', angle))
        def restoreState(self):
            calls.append('restoreState')
        def save(self):
            pass
        def setStrokeGray(self, *a, **k):
            pass
        def setLineWidth(self, *a, **k):
            pass
        def setStrokeColorRGB(self, *a, **k):
            pass
        def line(self, *a, **k):
            pass

    monkeypatch.setattr(gp.canvas, 'Canvas', RecCanvas)

    cfg = {
        'page_size': (10, 10),
        'margin_pt': 0,
        'gap_pt': 0,
        'card_width_pt': 1,
        'card_height_pt': 1,
        'GRID': (1, 1),
        'page_rotation_deg': 45,
    }
    pages = [[{'front': 'f1', 'back': 'b1'}]]

    gp.draw_pages('dummy.pdf', pages, cfg, front=True)

    assert not any(call[0] == 'rotate' for call in calls if isinstance(call, tuple))
