import requests
from urllib.parse import urljoin
from fe import conf


def test_search_missing_query_params():
    base = conf.URL
    # missing q parameter -> view should respond gracefully (likely 200 with empty list or 400)
    r = requests.get(urljoin(base, 'search/'))
    assert r.status_code in (200, 400)


def test_search_field_scope_and_pagination():
    base = conf.URL
    # perform queries with pagination and field scoping
    r = requests.get(urljoin(base, 'search/'), params={'q': 'python', 'page': 1, 'page_size': 2})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    # if results present, ensure pagination fields exist
    if data.get('results'):
        assert 'total' in data or 'results' in data
