from datetime import datetime
from app.entities.custom_topic_entity import CustomTopicEntity
from app.models.exceptions import CustomTopicValidationError

class CustomTopic:
    def __init__(self, name: str, id: int | None = None, created_at: datetime | None = None):
        self._id = id
        self.name = name 
        self._created_at = created_at

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value or not isinstance(value, str):
            raise CustomTopicValidationError("name", "não pode ser vazio.")

        name = " ".join(value.strip().split())

        if not name:
            raise CustomTopicValidationError("name", "não pode ser vazio após limpeza.")

        if len(name) > 100:
            raise CustomTopicValidationError("name", "deve ter no máximo 100 caracteres.")


        self._name = name

    def to_dict(self) -> dict:
        return {"id": self._id, "name": self._name, "created_at": self._created_at}

    @classmethod
    def from_entity(cls, e: CustomTopicEntity) -> "CustomTopic":
        if not e:
            return None
        return cls(
            id=e.id,
            name=e.name,
            created_at=e.created_at
        )

    def to_orm(self) -> CustomTopicEntity:
        return CustomTopicEntity(
            id=self._id,
            name=self._name,
            created_at=self._created_at
        )