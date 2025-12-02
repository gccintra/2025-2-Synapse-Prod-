import re
import json
import logging
from typing import Optional, Dict, List
from app.repositories.user_repository import UserRepository
from app.services.news_service import NewsService
from app.services.ai_service import AIService
from app.services.mail_service import MailService


class NewsletterService:
    """
    Service for newsletter generation and sending functionality.

    Responsibilities:
    - Orchestrate newsletter content generation
    - Generate AI-powered introductions and summaries
    - Build HTML email templates
    - Send individual newsletters
    """

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        news_service: Optional[NewsService] = None,
        ai_service: Optional[AIService] = None,
        mail_service: Optional[MailService] = None
    ):
        """
        Initialize NewsletterService with dependency injection.

        Args:
            user_repo: User repository for user data access
            news_service: Service for news data retrieval
            ai_service: Service for AI content generation
            mail_service: Service for email sending
        """
        self.user_repo = user_repo or UserRepository()
        self.news_service = news_service or NewsService()
        self.ai_service = ai_service or AIService()
        self.mail_service = mail_service or MailService()

    def send_newsletter_to_user(self, user) -> Dict[str, any]:
        """
        Main orchestration method for sending newsletter to a single user.

        Args:
            user: User object containing user information

        Returns:
            dict: {'success': bool, 'reason': str | None}
        """
        try:
            # Get personalized news for user
            news_data = self._get_user_news_data(user.id)

            if not news_data:
                return {
                    'success': False,
                    'reason': f'No news found for user {user.email}'
                }

            # Generate AI content with fallback
            ai_content = self._generate_ai_content_with_fallback(user, news_data)

            # Build newsletter HTML
            newsletter_html = self.build_newsletter_email(
                user_name=user.full_name,
                ai_content=ai_content,
                news_items=news_data
            )

            # Send email
            subject = "Your Weekly Synapse Digest - Top Stories & AI Insights"

            success = self.mail_service.sendemail(
                recipient_email=user.email,
                recipient_name=user.full_name,
                subject=subject,
                html_content=newsletter_html
            )

            if success:
                logging.info(f"✅ Newsletter sent successfully to {user.email}")
                return {'success': True, 'reason': None}
            else:
                return {
                    'success': False,
                    'reason': 'Email sending failed'
                }

        except Exception as e:
            logging.error(f"Error sending newsletter to {user.email}: {e}", exc_info=True)
            return {
                'success': False,
                'reason': f'Exception: {str(e)}'
            }

    def generate_newsletter_content(self, user, news_data: List[Dict]) -> Dict[str, any]:
        """
        Generate AI-powered newsletter content with fallback.

        Args:
            user: User object
            news_data: List of news articles

        Returns:
            dict: {'intro': str, 'summaries': list[str]}
        """
        return self._generate_ai_content_with_fallback(user, news_data)

    def build_newsletter_email(self, user_name: str, ai_content: Dict[str, any], news_items: List[Dict]) -> str:
        """
        Build complete HTML email template.

        Args:
            user_name: User's full name
            ai_content: Dict with 'intro' and 'summaries' keys
            news_items: List of news item dictionaries

        Returns:
            str: Complete HTML email content
        """
        # Format the AI introduction with HTML styling
        formatted_intro = self._format_ai_intro(ai_content.get("intro", ""))

        header = f"""
        <div style="margin-bottom:40px">
          <span
            style="
              display: block;
              font-weight: 700;
              font-size: clamp(40px, 8vw, 60px);
              font-family: 'Rajdhani', sans-serif;
              line-height: 0.8;
              text-align: center;
              margin-bottom: 5px;
            "
            >Synapse</span
          >
          <span
            style="
              display: block;
              font-size: clamp(18px, 4vw, 22px);
              font-family: 'Montserrat', sans-serif;
              font-weight: 400;
              margin-top: -3px;
              text-align: center;
              color: #000000;
            "
            >Newsletter</span
          >
        </div>
        <div
          style="
            margin: auto;
            width: 78%;
            font-family: 'Montserrat', sans-serif;
            border: 1.5px solid #222;
            border-radius: 4px;
            background: #ececec;
            padding: 16px 22px;
            margin-bottom: 36px;
          "
        >
          <div style="margin: 0;">
            {formatted_intro}
          </div>
        </div>
        """

        sections = []
        for i, item in enumerate(news_items):
            block = f"""
            <section style="margin-bottom: 38px">
              <div style="margin-bottom: 8px">
                <span
                  style="
                    font-size: 12px;
                    font-family: 'Montserrat', sans-serif;
                    color: #222;
                    text-transform: uppercase;
                    font-weight: 500;
                    border-bottom: 1px solid #999;
                    padding-bottom: 2px;
                    background: #ececec;
                  "
                  >{item['category']}</span
                >
              </div>
              <h2
                style="
                  margin: 2 0 8px 0;
                  font-family: 'Montserrat', sans-serif;
                  font-size: 18px;
                  font-weight: 600;
                "
              >
                <a href="{item['url']}"
                   target="_blank"
                   rel="noopener noreferrer"
                   style="
                     color: #181818;
                     text-decoration: none;
                     border-bottom: 1px solid transparent;
                     transition: all 0.2s ease;
                   "
                   onmouseover="this.style.borderColor='#007acc'; this.style.color='#007acc';"
                   onmouseout="this.style.borderColor='transparent'; this.style.color='#181818';">
                  {item['title']}
                </a>
              </h2>
              <img
                src="{item['img_url']}"
                alt="{item['title']}"
                style="
                  width: 100%;
                  max-width: 445px;
                  border-radius: 6px;
                  margin-bottom: 15px;
                  display: block;
                "
              />
              <p
                style="
                  color: #444;
                  margin: 0 0 16px 0;
                  font-family: 'Montserrat', sans-serif;
                  font-size: 14px;
                  line-height: 1.5;
                "
              >
                {ai_content["summaries"][i] if i < len(ai_content["summaries"]) else item.get('summary', 'Summary not available')}
              </p>
              <div style="margin-bottom: 12px;">
                <a href="{item['url']}"
                   target="_blank"
                   rel="noopener noreferrer"
                   style="
                     display: inline-block;
                     background: #007acc;
                     color: #ffffff;
                     padding: 10px 16px;
                     text-decoration: none;
                     border-radius: 4px;
                     font-family: 'Montserrat', sans-serif;
                     font-size: 13px;
                     font-weight: 500;
                     transition: background-color 0.2s ease;
                   "
                   onmouseover="this.style.backgroundColor='#005a99';"
                   onmouseout="this.style.backgroundColor='#007acc';">
                  Read Full Article →
                </a>
              </div>
              <div
                style="
                  color: #888;
                  margin-top: 8px;
                  border-top: 1px solid #eee;
                  padding-top: 7px;
                  font-family: 'Montserrat', sans-serif;
                  font-size: 10px;
                "
              >
                {item['source']} | {item['date']}
              </div>
            </section>
            """
            sections.append(block)

        html = f"""<!DOCTYPE html>
        <html lang="en" style="background-color: #fafafa">
          <head>
            <meta charset="UTF-8" />
            <title>Synapse Newsletter</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <link rel="preconnect" href="https://fonts.googleapis.com" />
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
            <link
              href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;700&display=swap"
              rel="stylesheet"
            />
            <link
              href="https://fonts.googleapis.com/css2?family=Montserrat:wght@200;400;500;600;700&display=swap"
              rel="stylesheet"
            />
          </head>
          <body
            style="margin: 0; padding: 0; background-color: #fafafa; color: #181818"
          >
            <div
              style="
                max-width: 600px;
                width: 90%;
                margin: 20px auto;
                background: #fff;
                box-shadow: 0 2px 8px rgba(60, 60, 67, 0.07);
                border-radius: 10px;
                padding: 40px 20px;
              "
            >
              {header}
              <div>
                <div style="max-width: 100%; margin: 0 auto; padding: 0 10px">
                  {"".join(sections)}
                </div>
              </div>
            </div>
          </body>
        </html>
        """

        return html

    def _get_user_news_data(self, user_id: int) -> List[Dict]:
        """
        Get personalized news data for a user.

        Args:
            user_id: User ID

        Returns:
            List of news dictionaries
        """
        try:
            return self.news_service.get_news_to_email(user_id, page=1, per_page=5)
        except Exception as e:
            logging.error(f"Error fetching news for user {user_id}: {e}")
            return []

    def generate_complete_newsletter_content(self, user, news_list, model: str = 'gemini-2.5-flash', temperature: float = 0.4) -> dict | None:
        """
        Gera introdução personalizada e resumos das notícias em uma única chamada de IA.

        Args:
            user: Objeto do usuário contendo informações pessoais
            news_list: Lista de notícias (dicionários com title, content, description, etc.)
            model: Modelo de IA a ser usado (padrão: 'gemini-2.5-flash')
            temperature: Temperatura para geração de conteúdo (padrão: 0.1)

        Returns:
            dict: {"intro": "texto_introdução", "summaries": ["resumo1", "resumo2", ...]}
            None: se houver erro ou modelo não disponível
        """
        if not news_list or len(news_list) == 0:
            logging.warning("Lista de notícias vazia para geração de conteúdo.")
            return None

        try:
            # Preparar dados das notícias para o prompt
            noticias_data = []
            for i, news in enumerate(news_list):
                # Priorizar content (texto completo) sobre summary (descrição curta)
                full_content = news.get('content', '').strip()
                short_summary = news.get('summary', '').strip()

                # Usar content se disponível, senão fallback para summary
                article_text = full_content if full_content else short_summary

                news_info = {
                    "index": i + 1,
                    "title": news.get('title', 'Title not available'),
                    "summary": short_summary,
                    "content": article_text[:1500]  # Aumentado limite para textos completos
                }
                noticias_data.append(news_info)

            # Criar prompt único que gera intro + resumos em inglês com conteúdo rico
            prompt = f"""
            You are an expert assistant specialized in creating personalized newsletters with rich, comprehensive content.

            USER: {user.full_name}

            TASK: Generate in English:
            1. A personalized and engaging introduction for the user (3-5 sentences)
            2. Rich, comprehensive summaries for each news article (4-6+ sentences each)

            SELECTED NEWS ARTICLES:
            {chr(10).join([f"ARTICLE {n['index']}: {n['title']}{chr(10)}Summary: {n['summary']}{chr(10)}Full Content: {n['content']}..." for n in noticias_data])}

            RESPONSE FORMAT (Valid JSON):
            {{
                "intro": "Hello {user.full_name}, [personalized and engaging introductory text]",
                "summaries": [
                    "Rich summary of article 1...",
                    "Rich summary of article 2...",
                    "Rich summary of article 3...",
                    "Rich summary of article 4...",
                    "Rich summary of article 5..."
                ]
            }}

            DETAILED INSTRUCTIONS FOR SUMMARIES:
            - Provide comprehensive analysis with context and background information
            - Add relevant industry insights, trends, and implications when applicable
            - Include potential impact on markets, society, or relevant stakeholders
            - Complement with related information not explicitly mentioned in the original article
            - Explain technical concepts in accessible language
            - Connect to broader themes or current events when relevant
            - Make each summary valuable, informative, and engaging (4-6+ sentences)
            - Maintain journalistic tone while being accessible and insightful

            INTRODUCTION INSTRUCTIONS:
            - Create a warm, personalized greeting for {user.full_name}
            - Reference the curated selection of articles
            - Build anticipation for the rich content that follows
            - Make a natural transition to the news summaries

            IMPORTANT: Respond ONLY with the JSON, no additional explanations.
            """

            logging.info(f"Gerando conteúdo completo do newsletter para {user.full_name} ({len(news_list)} notícias) - model: {model}, temperature: {temperature}")

            # Chamar AIService com os parâmetros especificados
            response_text = self.ai_service.generate_content(
                prompt=prompt,
                model=model,
                temperature=temperature
            )

            if not response_text:
                logging.warning("AIService retornou resposta vazia para geração de newsletter.")
                return None

            # Tentar fazer parse do JSON retornado
            try:
                # Remover possíveis markdown code blocks se existirem
                clean_response = response_text.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()

                ai_content = json.loads(clean_response)

                # Validar estrutura do retorno
                if not isinstance(ai_content, dict) or 'intro' not in ai_content or 'summaries' not in ai_content:
                    raise ValueError("Estrutura JSON inválida")

                if not isinstance(ai_content['summaries'], list) or len(ai_content['summaries']) != len(news_list):
                    raise ValueError("Número de resumos não corresponde ao número de notícias")

                logging.info(f"Conteúdo do newsletter gerado com sucesso para {user.full_name}")
                return ai_content

            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Erro ao parsear resposta JSON da IA: {e}. Resposta: {response_text[:200]}...")
                # Fallback: retornar estrutura básica em inglês
                return {
                    "intro": f"Hello {user.full_name}, here's your personalized selection of this week's most important news.",
                    "summaries": [news.get('description', 'Summary not available') for news in news_list]
                }

        except Exception as e:
            logging.error(f"Erro ao gerar conteúdo completo do newsletter: {e}", exc_info=True)
            # Fallback em caso de erro - em inglês
            return {
                "intro": f"Hello {user.full_name}, here's your personalized selection of this week's most important news.",
                "summaries": [news.get('description', 'Summary not available') for news in news_list]
            }

    def _generate_ai_content_with_fallback(self, user, news_data: List[Dict]) -> Dict[str, any]:
        """
        Generate AI content with fallback mechanism.

        Args:
            user: User object
            news_data: List of news articles

        Returns:
            dict: {'intro': str, 'summaries': list[str]}
        """
        try:
            ai_content = self.generate_complete_newsletter_content(user, news_data)

            if ai_content and isinstance(ai_content, dict) and 'intro' in ai_content:
                return ai_content
            else:
                logging.warning(f"AI service returned invalid content for {user.full_name}")
                return self._build_fallback_content(user, news_data)

        except Exception as e:
            logging.error(f"AI content generation failed for {user.full_name}: {e}")
            return self._build_fallback_content(user, news_data)

    def _build_fallback_content(self, user, news_data: List[Dict]) -> Dict[str, any]:
        """
        Build fallback content when AI generation fails.

        Args:
            user: User object
            news_data: List of news articles

        Returns:
            dict: {'intro': str, 'summaries': list[str]}
        """
        return {
            "intro": f"Hello {user.full_name}, here's your personalized selection of this week's most important news.",
            "summaries": [news.get('summary', 'Summary not available') for news in news_data]
        }

    def _format_ai_intro(self, intro_text: str) -> str:
        """
        Format AI-generated introduction text with HTML styling.

        Args:
            intro_text: Raw introduction text from AI

        Returns:
            str: Formatted HTML string with proper styling
        """
        if not intro_text:
            return ""

        # Convert line breaks to HTML breaks
        formatted = intro_text.replace('\n', '<br>')

        # Add emphasis to key phrases (basic pattern matching)
        formatted = re.sub(r'\b(Hello [^,]+)', r'<strong>\1</strong>', formatted)
        formatted = re.sub(r'\b(breaking news|top stories|important|significant|major)\b', r'<strong>\1</strong>', formatted, flags=re.IGNORECASE)

        # Wrap in styled paragraph
        formatted = f"""<p style="margin: 0; font-size: 14px; line-height: 1.6; color: #333;">
            {formatted}
        </p>"""

        return formatted