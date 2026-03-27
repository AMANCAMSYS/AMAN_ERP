import os
import requests

BASE_URL = os.getenv("AMAN_BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("AMAN_TEST_USER", "zzzz")
PASSWORD = os.getenv("AMAN_TEST_PASSWORD", "As123321")
COMPANY_CODE = os.getenv("AMAN_TEST_COMPANY_CODE", "ae4e964a")
TIMEOUT = int(os.getenv("AMAN_TEST_TIMEOUT", "30"))


def login_and_get_token() -> str:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD,
            "company_code": COMPANY_CODE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200, f"Login failed: {response.status_code} {response.text}"
    payload = response.json()
    token = payload.get("access_token")
    assert token, "Missing access_token"
    return token


def auth_headers() -> dict:
    token = login_and_get_token()
    return {"Authorization": f"Bearer {token}"}


def get_json(response: requests.Response):
    try:
        return response.json()
    except ValueError:
        assert False, f"Expected JSON response, got: {response.text[:200]}"
