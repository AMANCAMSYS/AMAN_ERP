"""Test successful login and token generation."""
try:
    from testsprite_tests._scenarios import tc001_login_success
except ModuleNotFoundError:
    from _scenarios import tc001_login_success

tc001_login_success()
