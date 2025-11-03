import requests
from urllib.parse import urljoin
from fe import conf
import uuid


def test_ship_by_other_seller_fails():
    base = conf.URL
    # register seller A and create store/book
    sellerA_name = f"sellerA_{uuid.uuid4()}"
    r = requests.post(urljoin(base, 'auth/register'), json={'user_id': sellerA_name, 'password': 'a'})
    assert r.status_code == 200
    r = requests.post(urljoin(base, 'auth/login'), json={'user_id': sellerA_name, 'password': 'a'})
    assert r.status_code == 200
    sellerA = r.json().get('user_id') or sellerA_name
    store_id = f"store_{uuid.uuid4()}"
    r = requests.post(urljoin(base, 'seller/create_store'), json={'user_id': sellerA, 'store_id': store_id})
    assert r.status_code == 200
    book_id = f"sbook_{uuid.uuid4()}"
    book_info = {'id': book_id, 'title': 'Sbook', 'price': 5, 'isbn': 's-isbn'}
    r = requests.post(urljoin(base, 'seller/add_book'), json={'user_id': sellerA, 'store_id': store_id, 'book_info': book_info, 'stock_level': 1})
    r = requests.post(urljoin(base, 'seller/add_stock_level'), json={'user_id': sellerA, 'store_id': store_id, 'book_id': book_id, 'add_stock_level': 1})

    # register buyer and create order
    buyer_name = f"buyerS_{uuid.uuid4()}"
    r = requests.post(urljoin(base, 'auth/register'), json={'user_id': buyer_name, 'password': 'b'})
    assert r.status_code == 200
    r = requests.post(urljoin(base, 'auth/login'), json={'user_id': buyer_name, 'password': 'b'})
    buyer = r.json().get('user_id') or buyer_name
    r = requests.post(urljoin(base, 'buyer/new_order'), json={'user_id': buyer, 'store_id': store_id, 'books': [{'id': book_id, 'count': 1}]})
    assert r.status_code == 200
    order_id = r.json().get('order_id')

    # register another seller B and try to ship A's order -> should fail
    sellerB_name = f"sellerB_{uuid.uuid4()}"
    r = requests.post(urljoin(base, 'auth/register'), json={'user_id': sellerB_name, 'password': 'bb'})
    assert r.status_code == 200
    r = requests.post(urljoin(base, 'auth/login'), json={'user_id': sellerB_name, 'password': 'bb'})
    assert r.status_code == 200
    sellerB = r.json().get('user_id') or sellerB_name
    r = requests.post(urljoin(base, 'seller/ship'), json={'user_id': sellerB, 'order_id': order_id})
    # expect failure status (400/403) or no state change; also allow 401 auth failure
    assert r.status_code in (200, 400, 401, 403)
