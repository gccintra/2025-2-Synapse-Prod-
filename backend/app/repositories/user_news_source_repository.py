import logging
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.entities.user_preferred_news_sources_entity import UserPreferredNewsSourceEntity
from app.models.exceptions import NewsSourceAlreadyAttachedError, NewsSourceNotAttachedError

class UserNewsSourceRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def attach(self, user_id: int, source_id: int):
        try:
            # Verifica se a relação já existe
            exists_stmt = select(UserPreferredNewsSourceEntity).where(UserPreferredNewsSourceEntity.user_id == user_id, UserPreferredNewsSourceEntity.source_id == source_id)
            existing = self.session.execute(exists_stmt).scalar_one_or_none()
            if existing:
                raise NewsSourceAlreadyAttachedError("A fonte de notícia já está associada a este usuário.")

            new_attachment = UserPreferredNewsSourceEntity(user_id=user_id, source_id=source_id)

            self.session.add(new_attachment)
            self.session.commit()
        except IntegrityError: # Caso a fonte ou usuário não exista, ou race condition
            self.session.rollback()
            logging.warning(f"Falha de integridade ao tentar associar usuário {user_id} com fonte {source_id}.")
            raise 
        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Erro de banco ao associar fonte a usuário: {e}", exc_info=True)
            raise

    def detach(self, user_id: int, source_id: int):
        try:
            stmt = delete(UserPreferredNewsSourceEntity).where(UserPreferredNewsSourceEntity.user_id == user_id, UserPreferredNewsSourceEntity.source_id == source_id)
            result = self.session.execute(stmt)
            self.session.commit()
            if result.rowcount == 0:
                raise NewsSourceNotAttachedError("Associação não encontrada para ser removida.") # Lança exceção se nada foi deletado
        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Erro de banco ao desassociar fonte de usuário: {e}", exc_info=True)
            raise

    def get_user_preferred_source_ids(self, user_id: int) -> list[int]:
        """
        Retorna lista de IDs das fontes preferidas do usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Lista de IDs das fontes preferidas pelo usuário
        """
        try:
            stmt = select(UserPreferredNewsSourceEntity.source_id).where(
                UserPreferredNewsSourceEntity.user_id == user_id
            )
            result = self.session.execute(stmt)
            source_ids = [row[0] for row in result.fetchall()]
            return source_ids
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar fontes preferidas do usuário {user_id}: {e}", exc_info=True)
            raise