import uuid
from be.model.user import User, jwt_encode


def new_user_id():
    return "test_user_branch_{}".format(uuid.uuid4())


def test_register_and_duplicate():
    u = User()
    uid = new_user_id()
    code, msg = u.register(uid, "pwd")
    assert code == 200

    # registering again should fail with exist user id
    code2, msg2 = u.register(uid, "pwd")
    assert code2 == 512


def test_change_password_wrong_old():
    u = User()
    uid = new_user_id()
    u.register(uid, "oldpwd")
    code, msg = u.change_password(uid, "badold", "newpwd")
    assert code == 401


def test_unregister_wrong_password():
    u = User()
    uid = new_user_id()
    u.register(uid, "pwd")
    code, msg = u.unregister(uid, "wrong")
    assert code == 401


def test_login_logout_and_check_token():
    u = User()
    uid = new_user_id()
    password = "pwd123"
    u.register(uid, password)

    # login with wrong password fails
    code, msg, token = u.login(uid, "badpwd", "term")
    assert code != 200

    # successful login returns token and check_token accepts it
    code, msg, token = u.login(uid, password, "termA")
    assert code == 200 and token
    c2, m2 = u.check_token(uid, token)
    assert c2 == 200

    # logout with invalid token should fail
    c3, m3 = u.logout(uid, "invalidtoken")
    assert c3 == 401


def test_private_check_token_invalid_signature():
    u = User()
    uid = new_user_id()
    u.register(uid, "pwd")
    # extract stored token
    cursor = u.conn.execute("SELECT token FROM user WHERE user_id = ?", (uid,))
    row = cursor.fetchone()
    assert row is not None
    token = row[0]

    # call the private checker with a different user id but with the same token
    # jwt.decode will fail because token was signed with the original user_id as key
    ok = u._User__check_token("attacker_user", token, token)
    assert ok is False
