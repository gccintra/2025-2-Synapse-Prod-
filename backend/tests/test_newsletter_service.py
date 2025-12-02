import pytest
from unittest.mock import MagicMock, patch, ANY
import json
from app.services.newsletter_service import NewsletterService


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.full_name = "John Doe"
    user.email = "john.doe@example.com"
    return user


@pytest.fixture
def mock_news_data():
    return [
        {
            "id": 101,
            "title": "News 1",
            "url": "http://news1.com",
            "summary": "Summary 1",
            "content": "Content 1",
            "img_url": "http://image1.com",
            "source": "Source 1",
            "category": "Tech",
            "date": "2025-01-01",
        },
        {
            "id": 102,
            "title": "News 2",
            "url": "http://news2.com",
            "summary": "Summary 2",
            "content": "Content 2",
            "img_url": "http://image2.com",
            "source": "Source 2",
            "category": "Business",
            "date": "2025-01-02",
        },
    ]


@pytest.fixture
def mock_ai_content():
    return {
        "intro": "Hello John Doe, here is your news digest.",
        "summaries": ["AI Summary 1", "AI Summary 2"],
    }


@pytest.fixture
def mock_dependencies():
    with patch('app.services.newsletter_service.UserRepository') as MockUserRepo, \
         patch('app.services.newsletter_service.NewsService') as MockNewsService, \
         patch('app.services.newsletter_service.AIService') as MockAIService, \
         patch('app.services.newsletter_service.MailService') as MockMailService:
        
        yield {
            "user_repo": MockUserRepo(),
            "news_service": MockNewsService(),
            "ai_service": MockAIService(),
            "mail_service": MockMailService(),
        }


def test_send_newsletter_to_user_happy_path(mock_dependencies, mock_user, mock_news_data, mock_ai_content):
    # Arrange
    mock_dependencies["news_service"].get_news_to_email.return_value = mock_news_data
    mock_dependencies["ai_service"].generate_content.return_value = json.dumps(mock_ai_content)
    mock_dependencies["mail_service"].sendemail.return_value = True

    service = NewsletterService(
        news_service=mock_dependencies["news_service"],
        ai_service=mock_dependencies["ai_service"],
        mail_service=mock_dependencies["mail_service"],
    )

    # Act
    result = service.send_newsletter_to_user(mock_user)

    # Assert
    assert result["success"] is True
    mock_dependencies["news_service"].get_news_to_email.assert_called_once_with(mock_user.id, page=1, per_page=5)
    mock_dependencies["ai_service"].generate_content.assert_called_once()
    mock_dependencies["mail_service"].sendemail.assert_called_once_with(
        recipient_email=mock_user.email,
        recipient_name=mock_user.full_name,
        subject=ANY,
        html_content=ANY
    )


def test_send_newsletter_no_news_found(mock_dependencies, mock_user):
    # Arrange
    mock_dependencies["news_service"].get_news_to_email.return_value = []
    service = NewsletterService(news_service=mock_dependencies["news_service"])

    # Act
    result = service.send_newsletter_to_user(mock_user)

    # Assert
    assert result["success"] is False
    assert f"No news found for user {mock_user.email}" in result["reason"]
    mock_dependencies["news_service"].get_news_to_email.assert_called_once_with(mock_user.id, page=1, per_page=5)


def test_send_newsletter_email_sending_fails(mock_dependencies, mock_user, mock_news_data, mock_ai_content):
    # Arrange
    mock_dependencies["news_service"].get_news_to_email.return_value = mock_news_data
    mock_dependencies["ai_service"].generate_content.return_value = json.dumps(mock_ai_content)
    mock_dependencies["mail_service"].sendemail.return_value = False
    service = NewsletterService(
        news_service=mock_dependencies["news_service"],
        ai_service=mock_dependencies["ai_service"],
        mail_service=mock_dependencies["mail_service"],
    )

    # Act
    result = service.send_newsletter_to_user(mock_user)

    # Assert
    assert result["success"] is False
    assert result["reason"] == "Email sending failed"


def test_send_newsletter_exception_handling(mock_dependencies, mock_user):
    # Arrange
    mock_dependencies["news_service"].get_news_to_email.side_effect = Exception("Database error")
    service = NewsletterService(news_service=mock_dependencies["news_service"])

    # Act
    result = service.send_newsletter_to_user(mock_user)

    # Assert
    assert result["success"] is False
    assert "Exception: Database error" in result["reason"]


def test_generate_complete_newsletter_content_success(mock_dependencies, mock_user, mock_news_data, mock_ai_content):
    # Arrange
    mock_dependencies["ai_service"].generate_content.return_value = json.dumps(mock_ai_content)
    service = NewsletterService(ai_service=mock_dependencies["ai_service"])

    # Act
    content = service.generate_complete_newsletter_content(mock_user, mock_news_data)

    # Assert
    assert content == mock_ai_content
    mock_dependencies["ai_service"].generate_content.assert_called_once()
    prompt = mock_dependencies["ai_service"].generate_content.call_args.kwargs['prompt']
    assert mock_user.full_name in prompt
    assert mock_news_data[0]['title'] in prompt


def test_generate_complete_newsletter_content_empty_news_list(mock_dependencies, mock_user):
    # Arrange
    service = NewsletterService(ai_service=mock_dependencies["ai_service"])

    # Act
    content = service.generate_complete_newsletter_content(mock_user, [])

    # Assert
    assert content is None
    mock_dependencies["ai_service"].generate_content.assert_not_called()


def test_generate_complete_newsletter_content_ai_failure(mock_dependencies, mock_user, mock_news_data):
    # Arrange
    mock_dependencies["ai_service"].generate_content.return_value = None
    service = NewsletterService(ai_service=mock_dependencies["ai_service"])

    # Act
    content = service.generate_complete_newsletter_content(mock_user, mock_news_data)

    # Assert
    assert content is None


def test_generate_complete_newsletter_content_json_error_fallback(mock_dependencies, mock_user, mock_news_data):
    # Arrange
    mock_dependencies["ai_service"].generate_content.return_value = "invalid json"
    service = NewsletterService(ai_service=mock_dependencies["ai_service"])

    # Act
    content = service.generate_complete_newsletter_content(mock_user, mock_news_data)

    # Assert
    assert "Hello John Doe" in content["intro"]
    assert len(content["summaries"]) == len(mock_news_data)
    assert content["summaries"][0] == mock_news_data[0]['summary']


def test_generate_ai_content_with_fallback_success(mock_dependencies, mock_user, mock_news_data, mock_ai_content):
    # Arrange
    service = NewsletterService(ai_service=mock_dependencies["ai_service"])
    service.generate_complete_newsletter_content = MagicMock(return_value=mock_ai_content)

    # Act
    content = service._generate_ai_content_with_fallback(mock_user, mock_news_data)

    # Assert
    assert content == mock_ai_content
    service.generate_complete_newsletter_content.assert_called_once_with(mock_user, mock_news_data)


def test_generate_ai_content_with_fallback_on_exception(mock_dependencies, mock_user, mock_news_data):
    # Arrange
    service = NewsletterService(ai_service=mock_dependencies["ai_service"])
    service.generate_complete_newsletter_content = MagicMock(side_effect=Exception("AI service down"))

    # Act
    content = service._generate_ai_content_with_fallback(mock_user, mock_news_data)

    # Assert
    assert "Hello John Doe" in content["intro"]
    assert len(content["summaries"]) == len(mock_news_data)
    assert content["summaries"][0] == mock_news_data[0]['summary']


def test_build_newsletter_email(mock_dependencies, mock_ai_content, mock_news_data):
    # Arrange
    service = NewsletterService(ai_service=mock_dependencies["ai_service"], mail_service=mock_dependencies["mail_service"])

    # Act
    html = service.build_newsletter_email("John Doe", mock_ai_content, mock_news_data)

    # Assert
    assert "<!DOCTYPE html>" in html
    assert "Synapse" in html
    assert "Newsletter" in html
    assert "<strong>Hello John Doe</strong>, here is your news digest." in html
    assert "News 1" in html
    assert "http://news1.com" in html
    assert "AI Summary 1" in html
    assert "News 2" in html
    assert "http://news2.com" in html
    assert "AI Summary 2" in html


def test_build_newsletter_email_with_fallback_summary(mock_dependencies, mock_news_data):
    # Arrange
    service = NewsletterService(ai_service=mock_dependencies["ai_service"], mail_service=mock_dependencies["mail_service"])
    ai_content = {
        "intro": "Test intro",
        "summaries": ["Only one summary"] # Less summaries than news items
    }

    # Act
    html = service.build_newsletter_email("John Doe", ai_content, mock_news_data)

    # Assert
    assert "Only one summary" in html
    assert mock_news_data[1]['summary'] in html # Fallback to original summary


def test_format_ai_intro():
    # Arrange
    service = NewsletterService(ai_service=MagicMock(), mail_service=MagicMock())
    intro_text = "Hello John Doe, here are your top stories.\nThis is important news."

    # Act
    formatted_intro = service._format_ai_intro(intro_text)

    # Assert
    assert "<strong>Hello John Doe</strong>" in formatted_intro
    assert "<strong>top stories</strong>" in formatted_intro
    assert "<strong>important</strong> news" in formatted_intro
    assert "<br>" in formatted_intro
    assert '<p style="margin: 0; font-size: 14px; line-height: 1.6; color: #333;">' in formatted_intro