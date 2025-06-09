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
