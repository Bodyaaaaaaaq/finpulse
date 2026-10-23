"""Залежності FastAPI, спільні для всіх ендпоінтів.

get_db дає сесію бази даних у кожен запит і гарантовано закриває її після.
Використання в роутері:

    @router.get("/something")
    def something(db: Session = Depends(get_db)):
        ...
"""
from app.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
