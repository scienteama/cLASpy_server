from app.services.ws_service import SocketIOService
from app.core.config import get_settings
from app.dao.recovery_dao import RecoveryDAO
import bcrypt
import logging
import secrets
from typing import List

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class RecoveryService:
    """Service de gestion des codes de récupération."""

    def __init__(self, recovery_dao: RecoveryDAO, ws_service: SocketIOService):
        self.config = get_settings()
        self.log = logging.getLogger("app")
        self.recovery_dao = recovery_dao
        self.ws_service = ws_service

    def generate_code(self, length: int = 12) -> str:
        """Génère un code aléatoire unique"""
        return "".join(secrets.choice(ALPHABET) for _ in range(length))

    def hash_code(self, code: str) -> str:
        """Hache un code avec bcrypt"""
        return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode()

    def format_code(self, code: str) -> str:
        """Formate un code en groupes de 4 (ex: ABCD-EFGH-IJKL)"""
        return "-".join(code[i : i + 4] for i in range(0, len(code), 4))

    async def generate_and_store_codes(
        self, user_id: int, count: int = 3, expiry_days: int = 180
    ) -> List[str]:
        """
        Génère ET stocke atomiquement les codes de récupération.

        Returns:
            List[str]: Codes en clair **UNIQUEMENT** pour affichage immédiat
                      (ils ne seront plus jamais accessibles)
        """
        if count < 1:
            raise ValueError("Must generate at least 1 recovery code")

        plain_codes: List[str] = []
        for _ in range(count):
            plain_codes.append(self.generate_code())

        code_hashes: List[str] = [self.hash_code(code) for code in plain_codes]

        await self.recovery_dao.add_batch(user_id, code_hashes, expiry_days)

        self.log.info(f"Generated {count} recovery codes for user {user_id}")
        return plain_codes

    def get_formatted_codes(self, codes: List[str]) -> List[str]:
        """Retourne les codes formatés pour affichage UI"""
        return [self.format_code(code) for code in codes]

    async def generate_and_display_codes(self, user_id: int) -> List[str]:
        """Retourne les codes formatés pour affichage UI"""
        codes = await self.generate_and_store_codes(user_id)
        return self.get_formatted_codes(codes)

    async def validate_recovery_code(self, email: str, code: str) -> int | None:
        normalized_code = code.replace("-", "").strip().upper()
        recovery_codes = await self.recovery_dao.get_valid_codes_by_email(email)

        if not recovery_codes:
            return None

        for recovery_code in recovery_codes:
            try:
                if bcrypt.checkpw(
                    normalized_code.encode("utf-8"),
                    recovery_code.code_hash.encode("utf-8"),
                ):
                    return recovery_code.id

            except (ValueError, TypeError):
                self.log.exception("Invalid bcrypt hash for recovery code")

        return None

    async def mark_as_used(self, recovery_code_id: int) -> None:
        await self.recovery_dao.mark_as_used(recovery_code_id)
