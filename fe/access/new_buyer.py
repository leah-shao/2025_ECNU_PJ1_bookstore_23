from fe import conf
from fe.access import buyer, auth


def register_new_buyer(user_id, password) -> buyer.Buyer:
    a = auth.Auth(conf.URL)
    code = a.register(user_id, password)
    # allow already-existing user (512) to be treated as success for tests
    assert code == 200 or code == 512
    s = buyer.Buyer(conf.URL, user_id, password)
    return s
