"""Test accessing API documentation/Swagger UI."""
try:
    from testsprite_tests._scenarios import tc_api_docs_access
except ModuleNotFoundError:
    from _scenarios import tc_api_docs_access

tc_api_docs_access()
