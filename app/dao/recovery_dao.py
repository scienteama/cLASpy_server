from datetime import timedelta, timezone, datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recovery import RecoveryCode
from app.models.user import User


class RecoveryDAO:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, user_id: int, code_hash: str):
        """Insertion unitaire."""

        now = datetime.now(timezone.utc)
        code = RecoveryCode(
            user_id=user_id,
            code_hash=code_hash,
            created_at=now,
            expires_at=now + timedelta(days=180),
        )

        self.db.add(code)
        await self.db.commit()
        await self.db.refresh(code)
        return code

    async def add_batch(self, user_id: int, code_hashes: List[str], expiry_days: int = 180):
        """Insertion batch de plusieurs codes pour un même user."""

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=expiry_days)

        recovery_codes = [
            RecoveryCode(
                user_id=user_id,
                code_hash=h,
                created_at=now,
                expires_at=expires_at,
                used_at=None,
            )
            for h in code_hashes
        ]

        self.db.add_all(recovery_codes)
        await self.db.commit()

        if recovery_codes:
            await self.db.refresh(recovery_codes[0])

        return recovery_codes

    async def get_valid_codes_by_email(self, email: str) -> List[RecoveryCode]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(RecoveryCode)
            .join(User, User.id == RecoveryCode.user_id)
            .where(
                User.email == email,
                RecoveryCode.used_at.is_(None),
                RecoveryCode.expires_at > now,
            )
        )

        return list(result.scalars().all())

    async def mark_as_used(self, recovery_code_id: int) -> None:
        result = await self.db.execute(
            select(RecoveryCode).where(RecoveryCode.id == recovery_code_id)
        )

        recovery_code = result.scalar_one_or_none()

        if recovery_code is None:
            return

        recovery_code.used_at = datetime.now(timezone.utc)

        await self.db.commit()
