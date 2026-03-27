"""Test accounting journal entries list with date range filter."""
try:
    from testsprite_tests._scenarios import tc_accounting_entries_date_range
except ModuleNotFoundError:
    from _scenarios import tc_accounting_entries_date_range

tc_accounting_entries_date_range()
