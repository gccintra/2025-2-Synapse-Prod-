import os
import logging
from datetime import datetime, timezone

from google.oauth2 import id_token
from google.auth.transport import requests

from app.extensions import db
from app.entities.user_entity import UserEntity
from app.models.exceptions import EmailInUseError
from app.entities.user_providers import UserProviderEntity


class GoogleAuthService:

    # -----------------------------
    # 1) VALIDAR TOKEN DO GOOGLE
    # -----------------------------
    def verify_google_token(self, token: str) -> dict:
        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")

            payload = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                client_id
            )

            return {
                "email": payload.get("email"),
                "full_name": payload.get("name"),
                "picture": payload.get("picture"),
                "sub": payload.get("sub"),  # Google UID
            }

        except Exception as e:
            logging.warning(f"Token Google inválido: {e}")
            raise ValueError("Token inválido ou expirado.")


    # --------------------------------------------
    # 2) FLUXO PRINCIPAL DE LOGIN VIA GOOGLE
    # --------------------------------------------
    def google_login(self, id_token_str: str) -> UserEntity:
        # 1. Validar token no Google
        google_data = self.verify_google_token(id_token_str)

        email = google_data["email"]
        google_uid = google_data["sub"]

        # 2. Verificar se já existe um provider Google para esse usuário
        provider = UserProviderEntity.query.filter_by(
            provider_name="google",
            provider_user_id=google_uid
        ).first()

        if provider:
            return provider.user  # Login direto

        # 3. Não existe provider ainda — verificar usuário pelo e-mail
        user = UserEntity.query.filter_by(email=email).first()

        if user:
            # Usuário já existe mas talvez tenha cadastro normal (senha)
            if user.password_hash is not None:
                raise EmailInUseError(
                    "Este e-mail já está em uso em uma conta sem Google Login."
                )
        else:
            # Criar novo usuário
            user = UserEntity(
                full_name=google_data["full_name"],
                email=email,
                password_hash="",  # vazio porque login é pelo Google
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(user)
            db.session.flush()

        # 4. Registrar o provedor Google
        new_provider = UserProviderEntity(
            user_id=user.id,
            provider_name="google",
            provider_user_id=google_uid,
            provider_email=email,
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(new_provider)
        db.session.commit()

        return user
