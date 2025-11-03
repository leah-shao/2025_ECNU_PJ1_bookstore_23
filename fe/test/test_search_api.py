import requests
from urllib.parse import urljoin
from fe import conf


def test_search_basic_and_pagination():
    url = urljoin(conf.URL, "search/")
    # basic search
    r = requests.get(url, params={"q": "python", "page": 1, "page_size": 3})
    assert r.status_code == 200
    js = r.json()
    assert js.get("total") is not None
    assert isinstance(js.get("results"), list)

    # pagination: page 2 should also return a list (maybe empty)
    r2 = requests.get(url, params={"q": "python", "page": 2, "page_size": 3})
    assert r2.status_code == 200
    js2 = r2.json()
    assert isinstance(js2.get("results"), list)
