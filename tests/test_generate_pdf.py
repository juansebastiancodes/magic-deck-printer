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
        def save(self):
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
