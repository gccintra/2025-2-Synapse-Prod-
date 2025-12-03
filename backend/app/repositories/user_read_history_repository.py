from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func, select, and_, desc
from datetime import datetime, timedelta, time 
import logging

from app.extensions import db
from app.entities.user_entity import UserEntity
from app.entities.news_entity import NewsEntity
from app.entities.user_read_history_entity import UserReadHistoryEntity
from app.models.exceptions import UserNotFoundError, NewsNotFoundError

class UserReadHistoryRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, user_id: int, news_id: int) -> tuple[UserReadHistoryEntity, bool]:
        try:
            existing_history = self.find_today_read(user_id, news_id)
            
            if existing_history:
                logging.info(f"Registro de leitura já existe hoje (user_id={user_id}, news_id={news_id}). Atualizando read_at.")
                updated_history = self.update_read_at(existing_history)
                return updated_history, False
            
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
            
            return history_entity, True
            
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
        
    def update_read_at(self, history_entity: UserReadHistoryEntity) -> UserReadHistoryEntity:
        try:
            history_entity.read_at = datetime.now()
            self.session.commit()
            self.session.refresh(history_entity)
            
            logging.info(f"Histórico atualizado: user_id={history_entity.user_id}, news_id={history_entity.news_id}, read_at={history_entity.read_at}")
            
            return history_entity
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Erro ao atualizar histórico: {e}", exc_info=True)
            raise Exception("Erro ao atualizar histórico de leitura.")
        
    def find_today_read(self, user_id: int, news_id: int) -> UserReadHistoryEntity | None:
        try:
            today_start = datetime.combine(datetime.today(), time.min)
            today_end = datetime.combine(datetime.today(), time.max)
            
            stmt = (
                select(UserReadHistoryEntity)
                .where(
                    and_(
                        UserReadHistoryEntity.user_id == user_id,
                        UserReadHistoryEntity.news_id == news_id,
                        UserReadHistoryEntity.read_at >= today_start,
                        UserReadHistoryEntity.read_at <= today_end
                    )
                )
                .order_by(desc(UserReadHistoryEntity.read_at))
            )
            
            result = self.session.execute(stmt).scalar_one_or_none()
            return result
            
        except SQLAlchemyError as e:
            logging.error(f"Erro ao buscar histórico do dia: {e}", exc_info=True)
            raise Exception("Erro ao verificar histórico do dia.")

   
    def get_user_history(
            self, 
            user_id: int, 
            page: int = 1, 
            per_page: int = 10
        ) -> tuple[list[tuple[UserReadHistoryEntity, NewsEntity]], int]:
        try:
            stmt = (
                select(UserReadHistoryEntity, NewsEntity)
                .join(NewsEntity, UserReadHistoryEntity.news_id == NewsEntity.id)
                .where(UserReadHistoryEntity.user_id == user_id)
                .options(joinedload(NewsEntity.source))
                .order_by(desc(UserReadHistoryEntity.read_at))
            )
            
            count_stmt = (
                select(func.count())
                .select_from(UserReadHistoryEntity)
                .where(UserReadHistoryEntity.user_id == user_id)
            )
            total = self.session.execute(count_stmt).scalar() or 0
            
            paginated_stmt = stmt.offset((page - 1) * per_page).limit(per_page)
            
            results = self.session.execute(paginated_stmt).all()
            
            logging.info(f"Histórico buscado: user_id={user_id}, page={page}, total={total}")
            
            return results, total
            
        except SQLAlchemyError as e:
            logging.error(f"Erro ao buscar histórico do usuário: {e}", exc_info=True)
            raise Exception("Erro ao buscar histórico de leitura.")

    def count_user_history(self, user_id: int) -> int:
        try:
            stmt = (
                select(func.count())
                .select_from(UserReadHistoryEntity)
                .where(UserReadHistoryEntity.user_id == user_id)
            )
            result = self.session.execute(stmt).scalar()
            return result or 0
        except SQLAlchemyError as e:
            logging.error(f"Erro ao contar histórico: {e}", exc_info=True)
            raise Exception("Erro ao contar histórico.")