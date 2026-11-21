from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.iam.passwords import WeakPasswordError
from app.modules.setup import service
from app.modules.setup.schemas import SetupRequest, SetupStatus

router = APIRouter(prefix="/api/v1/setup", tags=["setup"])


@router.get("/status", response_model=SetupStatus)
def setup_status(response: Response, db: Session = Depends(get_db)):
    """Does this installation still need first-run setup?"""
    response.headers["Cache-Control"] = "no-store"
    return SetupStatus(setup_required=service.is_setup_required(db))


@router.post("/complete", status_code=201)
def complete_setup(
    payload: SetupRequest, request: Request, db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    try:
        service.complete_setup(db, payload, ip)
        db.commit()
    except service.InvalidSetupCode:
        db.commit()  # keep the audit record of the failed attempt
        raise HTTPException(status_code=403, detail="Invalid setup code.")
    except (service.SetupAlreadyDone, IntegrityError):
        db.rollback()
        raise HTTPException(status_code=409, detail="Setup has already been completed.")
    except service.AccountAlreadyExists:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    except WeakPasswordError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error))
    return {"status": "completed"}