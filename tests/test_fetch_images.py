import types
import importlib
import sys

import pytest


@pytest.fixture
def fi(monkeypatch):
    # Provide minimal requests module before import
    req_mod = types.SimpleNamespace(get=lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, 'requests', req_mod)
    yaml_mod = types.ModuleType('yaml')
    yaml_mod.safe_load = lambda s: {}
    monkeypatch.setitem(sys.modules, 'yaml', yaml_mod)
    if 'fetch_images' in sys.modules:
        del sys.modules['fetch_images']
    return importlib.import_module('fetch_images')


class DummyResp:
    def __init__(self, data):
        self.data = data
        self.status_code = 200

    def json(self):
        return self.data


def test_append_lang(fi):
    url = 'http://example.com/image.png'
    assert fi._append_lang(url, 'es') == url + '?lang=es'
    url2 = 'http://example.com/image.png?foo=1'
    res = fi._append_lang(url2, 'es')
    assert res.startswith(url2)
    assert 'lang=es' in res


def test_fetch_single_card_lang(monkeypatch, fi, tmp_path):
    data = {
        'lang': 'es',
        'image_uris': {'png': 'http://img/image.png'},
        'name': 'Island',
        'printed_name': 'Isla',
    }

    def fake_get(url, params=None):
        assert params['lang'] in ('es', 'en')
        return DummyResp(data)

    downloaded = []

    def fake_download(url, dest):
        downloaded.append(url)
        path = tmp_path / dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('')

    monkeypatch.setattr(fi.requests, 'get', fake_get)
    monkeypatch.setattr(fi, 'download_image', fake_download)

    fi._fetch_single_card(1, 'Island', 'es')
    assert downloaded
    assert downloaded[0].endswith('lang=es')


def test_parse_card_list_extended(fi, tmp_path):
    data = (
        "1 Arcane Signet (FIC) 335\n"
        "2 Swamp\n"
        "1 Beast Within (PLST) BBD-190\n"
    )
    path = tmp_path / "cards.txt"
    path.write_text(data)

    cards = fi.parse_card_list(str(path))

    assert cards == [
        (1, 'Arcane Signet', 'FIC', '335'),
        (2, 'Swamp', None, None),
        (1, 'Beast Within', 'PLST', 'BBD-190'),
    ]


def test_fetch_single_card_with_set_and_collector(monkeypatch, fi, tmp_path):
    data = {
        'lang': 'en',
        'image_uris': {'png': 'http://img/image.png'},
        'name': 'Island',
    }

    called = {}

    def fake_get(url, params=None):
        called['url'] = url
        called['params'] = params
        return DummyResp(data)

    monkeypatch.setattr(fi.requests, 'get', fake_get)
    monkeypatch.setattr(fi, 'download_image', lambda u, d: None)

    fi._fetch_single_card(1, 'Island', 'en', set_code='m20', collector='123')

    assert called['url'].startswith('https://api.scryfall.com/cards/m20/123/en')
    assert called['params'] is None
