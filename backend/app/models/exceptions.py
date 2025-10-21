class DomainError(Exception):
    """Classe base para erros de domínio específicos da aplicação."""
    pass
 
class ValidationError(DomainError):
    """Classe base para erros de validação de campos em modelos de negócio."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Erro de validação em '{field}': {message}")
 
# --- User Exceptions ---
 
class UserValidationError(ValidationError):
    """Lançado quando um atributo do usuário falha na validação."""
    pass

class InvalidPasswordError(UserValidationError):
    """Lançado para erros de validação específicos da senha."""
    def __init__(self, message: str):
        super().__init__("password", message)

class UserNotFoundError(DomainError):
    """Lançado quando um usuário não é encontrado no banco de dados."""
    pass

class EmailInUseError(DomainError):
    """Lançado quando um e-mail já está em uso por outro usuário."""
    pass
 
# --- News Exceptions ---
 
class NewsValidationError(ValidationError):
    """Lançado quando um atributo de uma notícia falha na validação."""
    pass
 
class NewsNotFoundError(DomainError):
    """Lançado quando uma notícia não é encontrada."""
    pass

class NewsAlreadyFavoritedError(DomainError):
    """Lançado quando se tenta favoritar uma notícia que já é favorita."""
    pass

class NewsNotFavoritedError(DomainError):
    """Lançado quando se tenta desfavoritar uma notícia que não é favorita."""
    pass
 
# --- News Source Exceptions ---
 
class NewsSourceValidationError(ValidationError):
    """Lançado quando um atributo de uma fonte de notícia falha na validação."""
    pass
 
class NewsSourceNotFoundError(DomainError):
    """Lançado quando uma fonte de notícia não é encontrada."""
    pass
 
class NewsSourceAlreadyAttachedError(DomainError):
    """Lançado quando se tenta associar uma fonte que já está associada ao usuário."""
    pass
 
class NewsSourceNotAttachedError(DomainError):
    """Lançado quando se tenta desassociar uma fonte que não está associada."""
    pass
 
# --- Topic & Custom Topic Exceptions ---
 
class TopicValidationError(ValidationError):
    """Lançado quando um atributo de um tópico falha na validação."""
    pass
 
class TopicValidationError(ValidationError):
    """Lançado quando um atributo de um tópico falha na validação."""
    pass
 
class CustomTopicValidationError(TopicValidationError):
    """Exceção para erros de validação de tópico customizado (herda de TopicValidationError)."""
    pass

class TopicNotFoundError(DomainError):
    """Lançado quando um tópico não é encontrado."""
    pass
 
class TopicAlreadyAttachedError(DomainError):
    """Lançado quando se tenta associar um tópico que já está associado ao usuário."""
    pass
 
class TopicNotAttachedError(DomainError):
    """Lançado quando se tenta desassociar um tópico que não está associado."""
    pass