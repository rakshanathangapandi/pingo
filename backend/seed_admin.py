"""Seed the default admin user if none exists."""
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import User, UserRole


def main():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@pingo.com").first()
        if existing:
            print("Admin user already exists.")
            return
        user = User(
            email="admin@pingo.com",
            hashed_password=get_password_hash("admin1234"),
            full_name="Pingo Admin",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created admin user id={user.id} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()