from auth import login, verify_token
from config import DEBUG


def handle_login(request):
    username = request.get("username")
    password = request.get("password")

    user = login(username, password)

    if user:
        return {"status": "ok", "token": user["token"]}

    return {"status": "error"}


def get_user_profile(request):
    token = request.get("token")

    if verify_token(token):
        return {
            "name": "Admin",
            "email": "admin@example.com",
            "debug": DEBUG
        }

    return {"status": "unauthorized"}