from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func, select
from datetime import datetime 
import logging

from app.extensions import db
from app.entities.user_entity import UserEntity
from app.entities.news_entity import NewsEntity
from app.entities.user_read_history_entity import UserReadHistoryEntity
from app.models.exceptions import UserNotFoundError, NewsNotFoundError

class UserReadHistoryRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, user_id: int, news_id: int) -> UserReadHistoryEntity:
        try:
            user_exists = self.session.query(
                self.session.query(UserEntity).filter_by(id=user_id).exists()
            ).scalar()
            
            if not user_exists:
                raise UserNotFoundError(f"Usuário com ID {user_id} não encontrado.")
            
            news_exists = self.session.query(
                self.session.query(NewsEntity).filter_by(id=news_id).exists()
            ).scalar()
            
            if not news_exists:
                raise NewsNotFoundError(f"Notícia com ID {news_id} não encontrada.")
            
            history_entity = UserReadHistoryEntity(
                user_id=user_id,
                news_id=news_id,
                read_at=datetime.now()
            )
            
            self.session.add(history_entity)
            self.session.commit()
            self.session.refresh(history_entity)
            
            logging.info(f"Histórico de leitura criado: user_id={user_id}, news_id={news_id}, read_at={history_entity.read_at}")
            
            return history_entity
            
        except (UserNotFoundError, NewsNotFoundError):
            self.session.rollback()
            raise
        except IntegrityError as e:
            self.session.rollback()
            logging.error(f"Erro de integridade ao criar histórico: {e}", exc_info=True)
            raise Exception("Erro de integridade ao salvar histórico de leitura.")
        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Erro de banco ao criar histórico: {e}", exc_info=True)
            raise Exception("Erro ao salvar histórico de leitura no banco de dados.")

   