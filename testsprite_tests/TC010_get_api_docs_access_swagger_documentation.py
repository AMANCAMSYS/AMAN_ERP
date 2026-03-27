"""Test accessing API documentation/Swagger UI."""
try:
    from testsprite_tests._scenarios import tc_root_backend_response, tc_api_docs_access
except ModuleNotFoundError:
    from _scenarios import tc_root_backend_response, tc_api_docs_access

# Test docs endpoint
tc_api_docs_access()
