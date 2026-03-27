"""Test purchase orders creation."""
try:
    from testsprite_tests._scenarios import tc_purchases_orders_create
except ModuleNotFoundError:
    from _scenarios import tc_purchases_orders_create

tc_purchases_orders_create()
