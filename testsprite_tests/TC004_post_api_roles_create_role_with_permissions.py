"""Test creating role with permissions."""
try:
    from testsprite_tests._scenarios import tc_roles_create_with_permissions
except ModuleNotFoundError:
    from _scenarios import tc_roles_create_with_permissions

tc_roles_create_with_permissions()
