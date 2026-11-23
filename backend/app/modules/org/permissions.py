from app.modules.iam.registry import Permission, declare

VIEW = "org.node.view"
EXPORT = "org.node.export"
CREATE = "org.node.create"
UPDATE = "org.node.update"
ARCHIVE = "org.node.archive"
MOVE = "org.node.move"
DELETE = "org.node.delete"
IMPORT = "org.node.import"
INITIALIZE = "org.node.initialize"

declare(
    Permission(
        VIEW,
        "View the organization structure",
        roles=("registrar", "dean", "cod", "lecturer", "auditor"),
    ),
    Permission(
        EXPORT,
        "Export parts of the organization structure",
        roles=("registrar", "dean", "cod", "auditor"),
    ),
    Permission(
        CREATE, "Add entries to the organization structure", roles=("registrar", "dean")
    ),
    Permission(
        UPDATE, "Rename entries and change their codes", roles=("registrar", "dean")
    ),
    Permission(ARCHIVE, "Archive and restore entries", roles=("registrar", "dean")),
    Permission(MOVE, "Move entries to a different parent", roles=("registrar",)),
    Permission(DELETE, "Delete unused entries", roles=("registrar",)),
    Permission(IMPORT, "Bulk import entries from a file", roles=("registrar", "dean")),
    Permission(INITIALIZE, "Set up the initial organization structure"),
)