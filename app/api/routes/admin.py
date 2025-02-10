from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_cache_db, get_main_db
from app.api.middleware.auth import (
    get_current_admin,
    create_access_token,
    verify_password,
)
from app.db.schemas.admin import Token
from app.db.models.admin import Admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/login", response_model=Token)
async def login_admin(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_main_db)
):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/clear-cache")
async def clear_cache(
    current_admin: Admin = Depends(get_current_admin),
    cache_db: Session = Depends(get_cache_db),
):
    """Clear the URL cache table"""
    try:
        cache_db.execute(text("TRUNCATE TABLE url_cache"))
        cache_db.commit()
        logger.info(
            f"URL cache cleared successfully by admin: {current_admin.username}"
        )
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing URL cache: {str(e)}")
        cache_db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
