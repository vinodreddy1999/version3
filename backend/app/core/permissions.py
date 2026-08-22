PERMISSION_CATALOG: list[tuple[str, str]] = [
    ("inventory:read", "View items, stock balances, and movements"),
    ("inventory:write", "Manage items and post stock movements"),
    ("warehouse:read", "View warehouses, zones, bins, and bin stock"),
    ("warehouse:write", "Manage warehouse structure and putaway/pick tasks"),
    ("production:read", "View BOMs, work centers, and production orders"),
    ("production:write", "Manage BOMs and complete production orders"),
    ("procurement:read", "View suppliers and purchase orders"),
    ("procurement:write", "Manage suppliers and process purchase orders"),
    ("sales:read", "View customers and sales orders"),
    ("sales:write", "Manage customers and process sales orders"),
    ("maintenance:read", "View assets and maintenance work orders"),
    ("maintenance:write", "Manage assets and the work order lifecycle"),
    ("quality:read", "View inspections and defects"),
    ("quality:write", "Log inspections and resolve defects"),
    ("admin:manage_users", "Invite, update, and deactivate users"),
    ("admin:manage_roles", "Create roles and assign permissions"),
]

PERMISSION_CODES = {code for code, _ in PERMISSION_CATALOG}
