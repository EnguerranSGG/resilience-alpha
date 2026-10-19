"""Annuaire d'utilisateurs **fictifs** chargé depuis un secret local.

Format du secret (une ligne par compte) : ``utilisateur:motdepasse[:role,role]``.
Les mots de passe sont hachés (scrypt) en mémoire au démarrage puis oubliés.

TODO(P1) : persister les comptes dans PostgreSQL si le scénario le nécessite.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass

_USERNAME = re.compile(r"^[a-z][a-z0-9_-]{2,31}$")
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


@dataclass(frozen=True)
class User:
    username: str
    roles: tuple[str, ...]
    salt: bytes
    password_hash: bytes


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)


class InvalidUserSpecError(ValueError):
    pass


class UserStore:
    def __init__(self, users: dict[str, User]) -> None:
        self._users = users
        self._dummy_salt = secrets.token_bytes(16)
        self._dummy_hash = _hash(secrets.token_urlsafe(16), self._dummy_salt)

    @classmethod
    def from_spec(cls, spec: str | None) -> UserStore:
        users: dict[str, User] = {}
        for line_no, raw in enumerate((spec or "").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) not in (2, 3):
                raise InvalidUserSpecError(f"ligne {line_no} : format attendu user:password[:roles]")
            username, password = parts[0], parts[1]
            if not _USERNAME.match(username) or len(password) < 12:
                raise InvalidUserSpecError(f"ligne {line_no} : identifiant ou mot de passe invalide")
            roles = tuple(r for r in (parts[2].split(",") if len(parts) == 3 else ["customer"]) if r)
            salt = secrets.token_bytes(16)
            users[username] = User(username, roles, salt, _hash(password, salt))
        return cls(users)

    def __len__(self) -> int:
        return len(self._users)

    def authenticate(self, username: str, password: str) -> User | None:
        user = self._users.get(username)
        if user is None:
            # Calcul factice pour ne pas révéler l'existence d'un compte par le temps de réponse.
            hmac.compare_digest(_hash(password, self._dummy_salt), self._dummy_hash)
            return None
        if hmac.compare_digest(_hash(password, user.salt), user.password_hash):
            return user
        return None
