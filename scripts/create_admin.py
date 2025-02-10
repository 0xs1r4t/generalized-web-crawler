import os
import sys
from dotenv import load_dotenv
from pathlib import Path


# Setup environment first
def setup_project_path():
    """Add project root to Python path"""
    project_root = str(Path(__file__).parent.parent)
    sys.path.append(project_root)


setup_project_path()
load_dotenv()

from sqlalchemy.orm import Session
from app.db.session import MainSessionLocal, get_engine
from app.db.models.admin import Admin, Base
from app.api.middleware.auth import get_password_hash


def init_db():
    """Create tables if they don't exist"""
    try:
        print("Initializing database tables...")
        Base.metadata.create_all(bind=get_engine())
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        raise


def create_admin(db: Session, username: str, password: str):
    try:
        hashed_password = get_password_hash(password)
        admin = Admin(username=username, password=hashed_password)
        db.add(admin)
        db.commit()
        print(f"Admin user '{username}' created successfully")
        return admin
    except Exception as e:
        print(f"Error creating admin: {str(e)}")
        db.rollback()
        raise


if __name__ == "__main__":
    # Ensure required environment variables are set
    required_vars = [
        "PRODUCT_DATABASE_URL",
        "CACHE_DATABASE_URL",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        sys.exit(1)

    # Initialize database tables
    print("Initializing database tables...")
    init_db()

    # Create admin user
    db = MainSessionLocal()
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    try:
        create_admin(db, admin_username, admin_password)
    finally:
        db.close()
