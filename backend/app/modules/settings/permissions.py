from app.modules.iam.registry import Permission, declare

UNIVERSITY_VIEW = "settings.university.view"
UNIVERSITY_UPDATE = "settings.university.update"
GENERAL_VIEW = "settings.general.view"
GENERAL_UPDATE = "settings.general.update"

declare(
    Permission(
        UNIVERSITY_VIEW,
        "View the university profile and appearance",
        roles=("registrar", "auditor"),
    ),
    Permission(UNIVERSITY_UPDATE, "Change the university profile, logo and colours"),
    Permission(
        GENERAL_VIEW, "View general settings", roles=("registrar", "auditor")
    ),
    Permission(GENERAL_UPDATE, "Change general settings"),
)