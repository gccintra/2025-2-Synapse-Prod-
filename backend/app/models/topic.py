from datetime import datetime
from app.entities.topic_entity import TopicEntity
from app.models.exceptions import TopicValidationError

class Topic:
    def __init__(self, name: str, state: int = 0, id: int | None = None, created_at: datetime | None = None):
        self.id = id
        self.name = name
        self.state = state
        self.created_at = created_at

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value or not isinstance(value, str):
            raise TopicValidationError("name", "não pode ser vazio.")
        name = " ".join(value.strip().split())
        if len(name) == 0 or len(name) > 255:
            raise TopicValidationError("name", "tamanho inválido (1..255).")
        self._name = name

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, value: int):
        try:
            iv = int(value)
        except (ValueError, TypeError):
            raise TopicValidationError("state", "deve ser inteiro.")
        if iv < 0 or iv > 32767:
            raise TopicValidationError("state", "fora do intervalo de SMALLINT.")
        self._state = iv

    @classmethod
    def from_entity(cls, e: TopicEntity) -> "Topic":
        if not e:
            return None
        return cls(id=e.id, name=e.name, state=e.state, created_at=e.created_at)

    def to_orm(self) -> TopicEntity:
        return TopicEntity(id=self.id, name=self.name, state=self.state, created_at=self.created_at)
