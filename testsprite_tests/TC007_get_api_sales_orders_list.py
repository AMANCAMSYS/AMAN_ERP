"""Test retrieving sales orders with status filter."""
try:
    from testsprite_tests._scenarios import tc_sales_orders_open_status
except ModuleNotFoundError:
    from _scenarios import tc_sales_orders_open_status

tc_sales_orders_open_status()
