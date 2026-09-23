import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def main():
    db = SessionLocal()
    email = "admin@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("Creating admin user...")
        user = User(
            email=email,
            full_name="System Admin",
            hashed_password=hash_password("Admin123!"),
            role="admin",
            is_active=True
        )
        db.add(user)
        db.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists. Resetting password to Admin123! for testing.")
        user.hashed_password = hash_password("Admin123!")
        db.commit()
    db.close()

if __name__ == "__main__":
    main()
