import requests
import uuid
from urllib.parse import urljoin
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe import conf


class TestOrderLifecycle:
    def setup_method(self):
        self.seller_id = "test_order_seller_{}".format(str(uuid.uuid1()))
        self.store_id = "test_order_store_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_order_buyer_{}".format(str(uuid.uuid1()))
        self.seller = register_new_seller(self.seller_id, self.seller_id)
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_id)
        # create store and add books
        self.gen = GenBook(self.seller_id, self.store_id)

    def test_cancel_before_payment(self):
        ok, buy_list = self.gen.gen(non_exist_book_id=False, low_stock_level=False)
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_list)
        assert code == 200

        # cancel via API
        url = urljoin(conf.URL, "buyer/cancel_order")
        headers = {"token": self.buyer.token}
        r = requests.post(url, headers=headers, json={"user_id": self.buyer_id, "order_id": order_id})
        assert r.status_code == 200

    def test_full_flow_ship_receive_and_query(self):
        ok, buy_list = self.gen.gen(non_exist_book_id=False, low_stock_level=False)
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_list)
        assert code == 200

        # compute order total deterministically from order details and add funds accordingly
        qurl = urljoin(conf.URL, "buyer/query_orders")
        params = {"user_id": self.buyer_id}
        r = requests.get(qurl, params=params)
        assert r.status_code == 200
        js = r.json()
        orders = js.get("orders", [])
        total_price = 0
        for o in orders:
            if o.get("order_id") == order_id:
                for d in o.get("details", []):
                    total_price += d.get("price", 0) * d.get("count", 0)
                break

        # add funds equal to total + small margin
        rcode = self.buyer.add_funds(total_price + 100)
        assert rcode == 200

        # pay
        rcode = self.buyer.payment(order_id)
        assert rcode == 200

        # seller ship via endpoint
        ship_url = urljoin(conf.URL, "seller/ship")
        headers = {"token": self.seller.token}
        r = requests.post(ship_url, headers=headers, json={"user_id": self.seller_id, "order_id": order_id})
        assert r.status_code == 200

        # buyer receive
        recv_url = urljoin(conf.URL, "buyer/receive")
        headers = {"token": self.buyer.token}
        r = requests.post(recv_url, headers=headers, json={"user_id": self.buyer_id, "order_id": order_id})
        assert r.status_code == 200

        # query orders and check status
        qurl = urljoin(conf.URL, "buyer/query_orders")
        params = {"user_id": self.buyer_id}
        r = requests.get(qurl, params=params)
        assert r.status_code == 200
        js = r.json()
        orders = js.get("orders", [])
        # find our order and check status
        found = False
        for o in orders:
            if o.get("order_id") == order_id:
                found = True
                assert o.get("status") == "received"
        assert found
