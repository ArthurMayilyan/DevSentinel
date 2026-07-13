def login(username, password):
    if username == "admin" and password == "admin":
        return {"token": "fake-jwt-token"}

    return None


def verify_token(token):
    if token:
        return True

    return False