from app.modules.iam.registry import Permission, declare, declare_labels

UNIVERSITY_VIEW = "settings.university.view"
UNIVERSITY_UPDATE = "settings.university.update"
GENERAL_VIEW = "settings.general.view"
GENERAL_UPDATE = "settings.general.update"

declare_labels(
    {
        "settings": "Settings",
        "settings.university": "University profile and appearance",
        "settings.general": "General settings",
    }
)

declare(
    Permission(
        UNIVERSITY_VIEW,
        "View the university profile and appearance",
        roles=("registrar", "auditor"),
    ),
    Permission(
        UNIVERSITY_UPDATE,
        "Change the university profile, logo and colours",
        risk="sensitive",
    ),
    Permission(
        GENERAL_VIEW, "View general settings", roles=("registrar", "auditor")
    ),
    Permission(GENERAL_UPDATE, "Change general settings", risk="sensitive"),
)