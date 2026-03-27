"""Test invalid login credentials handling."""
try:
    from testsprite_tests._scenarios import tc002_login_invalid_credentials
except ModuleNotFoundError:
    from _scenarios import tc002_login_invalid_credentials

tc002_login_invalid_credentials()
