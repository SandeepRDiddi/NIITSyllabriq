from __future__ import annotations

from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.db.session import get_session
from app.models.user import User


http_bearer = HTTPBearer(auto_error=False)


class AuthService:
    def authenticate(self, session: Session, email: str, password: str) -> str:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return create_access_token(subject=user.email, extra_claims={"role": user.role})

    def create_user(self, session: Session, email: str, full_name: str, role: str, password: str) -> User:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            raise ValueError("User already exists")
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            password_hash=hash_password(password),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def ensure_seed_users(self, session: Session) -> None:
        seed_users = [
            ("admin@niit.com", "Platform Admin", "admin", "Admin@123"),
            ("designer@niit.com", "Design Author", "designer", "Designer@123"),
            ("primary.reviewer@niit.com", "Primary Reviewer", "primary_reviewer", "Reviewer@123"),
            ("final.reviewer1@niit.com", "Final Reviewer One", "final_reviewer", "Reviewer@123"),
            ("final.reviewer2@niit.com", "Final Reviewer Two", "final_reviewer", "Reviewer@123"),
        ]
        for email, full_name, role, password in seed_users:
            user = session.exec(select(User).where(User.email == email)).first()
            if not user:
                session.add(
                    User(
                        email=email,
                        full_name=full_name,
                        role=role,
                        password_hash=hash_password(password),
                        is_active=True,
                    )
                )
        session.commit()


auth_service = AuthService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    session: Session = Depends(get_session),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_roles(allowed_roles: List[str]):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency
