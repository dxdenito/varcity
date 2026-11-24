from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.iam import role_service as errors


def execute(db: Session, action):
    try:
        result = action()
        db.commit()
        return result
    except errors.RoleNotFound as error:
        db.rollback()
        raise HTTPException(status_code=404, detail=error.message)
    except errors.RoleForbidden as error:
        db.rollback()
        raise HTTPException(status_code=403, detail=error.message)
    except errors.RoleConflict as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=error.message)
    except errors.RoleInvalid as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=error.message)
    except errors.RoleReauth as error:
        db.rollback()
        raise HTTPException(status_code=428, detail=error.message)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="That change conflicts with existing data."
        )