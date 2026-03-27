"""Test authorized access to companies list."""
try:
    from testsprite_tests._scenarios import tc_companies_authorized_access
except ModuleNotFoundError:
    from _scenarios import tc_companies_authorized_access

tc_companies_authorized_access()
