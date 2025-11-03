from be.model.user import User, jwt_encode
from be.model import store as model_store


def setup_function(fn):
    conn = model_store.get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM user;")
    conn.commit()


def test_register_and_duplicate():
    u = User()
    code, msg = u.register("u_test", "pw")
    assert code == 200
    # duplicate register should return exist-user error (512)
    code, msg = u.register("u_test", "pw")
    assert code == 512


def test_check_password_and_login_logout_change_unregister():
    u = User()
    # register fresh user
    code, msg = u.register("u_flow", "secret")
    assert code == 200

    # wrong password
    code, msg = u.check_password("u_flow", "bad")
    assert code == 401

    # correct password
    code, msg = u.check_password("u_flow", "secret")
    assert code == 200

    # login returns token
    code, msg, token = u.login("u_flow", "secret", "term1")
    assert code == 200
    assert token != ""

    # check_token should accept it
    code, msg = u.check_token("u_flow", token)
    assert code == 200

    # logout should succeed
    code, msg = u.logout("u_flow", token)
    assert code == 200

    # change password with wrong old -> expect 401
    code, msg = u.change_password("u_flow", "wrong_old", "newp")
    assert code == 401

    # change password with correct old
    code, msg = u.change_password("u_flow", "secret", "newp")
    assert code == 200

    # unregister with wrong password
    code, msg = u.unregister("u_flow", "no")
    assert code == 401

    # unregister with correct new password
    code, msg = u.unregister("u_flow", "newp")
    assert code == 200
