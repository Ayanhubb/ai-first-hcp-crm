"""Seed minimal demo users / HCPs / products for local integration testing.

Run from backend with PYTHONPATH including repo root::

    python ../scripts/seed_demo.py

Never use in production.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import get_session_factory, init_db  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.hcp import HealthcareProfessional  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security.passwords import hash_password  # noqa: E402

MR_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111112")
HCP_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
PRODUCT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

# Demo plaintext used only for local/dev seeding (documented in README later).
DEMO_PASSWORD = "Password123!"


def main() -> None:
    settings = get_settings()
    init_db(settings)
    session = get_session_factory()()
    try:
        if session.get(User, MR_ID) is None:
            session.add(
                User(
                    id=MR_ID,
                    email="ayan.mr@example.com",
                    full_name="Ayan Pal",
                    role=UserRole.MR,
                    password_hash=hash_password(DEMO_PASSWORD),
                    is_active=True,
                )
            )
        if session.get(User, ADMIN_ID) is None:
            session.add(
                User(
                    id=ADMIN_ID,
                    email="admin@example.com",
                    full_name="System Admin",
                    role=UserRole.ADMIN,
                    password_hash=hash_password(DEMO_PASSWORD),
                    is_active=True,
                )
            )
        if session.get(HealthcareProfessional, HCP_ID) is None:
            session.add(
                HealthcareProfessional(
                    id=HCP_ID,
                    first_name="Priya",
                    last_name="Sharma",
                    specialty="Cardiology",
                    institution="City Heart Clinic",
                    city="Mumbai",
                    state="MH",
                    country="IN",
                )
            )
        if session.get(Product, PRODUCT_ID) is None:
            session.add(
                Product(
                    id=PRODUCT_ID,
                    code="CARD-ATO-10",
                    name="AtorvaCare 10mg",
                    therapeutic_area="Cardiology",
                    is_active=True,
                )
            )
        # Ensure at least one product name for fuzzy AI grounding exists.
        existing = session.scalar(select(Product).where(Product.code == "CARD-ATO-20"))
        if existing is None:
            session.add(
                Product(
                    id=uuid.UUID("33333333-3333-3333-3333-333333333334"),
                    code="CARD-ATO-20",
                    name="AtorvaCare 20mg",
                    therapeutic_area="Cardiology",
                    is_active=True,
                )
            )
        session.commit()
        print("Seed complete. Demo MR: ayan.mr@example.com / Password123!")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
