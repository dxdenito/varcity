from sqlalchemy import delete, select

from app.core.db import SessionLocal
from app.modules.iam.rbac_models import Role, RolePermission

with SessionLocal() as db:
    role = db.scalar(select(Role).where(Role.system_key == "staff_member"))
    if role is None:
        raise SystemExit("Staff Member does not exist yet. Restart the server once and it will be created correctly.")
    db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    db.add(RolePermission(role_id=role.id, permission_code="org.node.view"))
    db.commit()
    print("Staff Member now holds org.node.view only")