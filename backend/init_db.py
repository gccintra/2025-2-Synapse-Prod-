from app import create_app
from app.extensions import db # Correção aqui
from app.models.topic import Topic
from app.repositories.topic_repository import TopicRepository

STANDARD_TOPICS = [
    'Technology', 'Crypto', 'Games', 'Economy', 'Business',
    'Science', 'Entertainment', 'World'
]

def init_db():
    app = create_app()
    with app.app_context():
        print("--- Iniciando Migração do Banco de Dados ---")
        db.create_all()
        print("--- Tabelas Criadas/Verificadas ---")

        print("Verificando e inicializando tópicos padrão...")
        topic_repo = TopicRepository()

        try:
            existing_topic_names = {t.name.lower() for t in topic_repo.list_all()}

            new_topics_created_count = 0
            for topic_name in STANDARD_TOPICS:
                if topic_name.lower() not in existing_topic_names:
                    try:
                        topic = Topic(name=topic_name, state=1)  
                        created_topic = topic_repo.create(topic)
                        print(f"Tópico padrão criado: '{created_topic.name}'")
                        new_topics_created_count += 1
                    except Exception as e:
                        print(f"Erro ao criar tópico '{topic_name}': {e}")
            
            if new_topics_created_count == 0:
                print("Todos os tópicos padrão já existem.")
                
        except Exception as e:
            print(f"Erro na inicialização dos tópicos: {e}")
            
        print("--- Inicialização Concluída ---")

if __name__ == "__main__":
    init_db()