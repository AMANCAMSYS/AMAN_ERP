"""Test treasury transaction transfer creation."""
try:
    from testsprite_tests._scenarios import tc_treasury_transfer_create
except ModuleNotFoundError:
    from _scenarios import tc_treasury_transfer_create

tc_treasury_transfer_create()
