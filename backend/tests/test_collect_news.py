import pytest
from unittest.mock import patch, MagicMock
import sys
import runpy

import app.jobs.collect_news


@pytest.fixture
def mock_app_context():
    with patch('app.create_app') as mock_create_app:
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__.return_value = mock_app
        mock_create_app.return_value = mock_app
        yield mock_create_app

@pytest.fixture(autouse=True)
def mock_news_collect_service():
    mock_service_class = MagicMock(name="NewsCollectServiceClass")
    mock_service_instance = MagicMock(name="NewsCollectServiceInstance")
    mock_service_class.return_value = mock_service_instance

    mock_module = MagicMock(name="MockNewsCollectServiceModule")
    mock_module.NewsCollectService = mock_service_class

    with patch.dict(sys.modules, {'app.services.news_collect_service': mock_module}):
        yield mock_service_instance


def test_run_collection_job_successful(mock_app_context, mock_news_collect_service):

    mock_news_collect_service.collect_news_simple.return_value = (5, 2)

    with patch('app.jobs.collect_news.logging') as mock_logging:
        app.jobs.collect_news.run_collection_job()

    mock_news_collect_service.collect_news_simple.assert_called_once()

def test_run_collection_job_with_exception(mock_app_context, mock_news_collect_service):

    mock_news_collect_service.collect_news_simple.side_effect = Exception("API connection error")

    with patch('app.jobs.collect_news.logging'):
        with pytest.raises(Exception, match="API connection error"):
            app.jobs.collect_news.run_collection_job()

    mock_news_collect_service.collect_news_simple.assert_called_once()

def test_main_block_runs_run_collection_job(mock_app_context, mock_news_collect_service):
    mock_news_collect_service.collect_news_simple.return_value = (1, 1)

    runpy.run_module('app.jobs.collect_news', run_name='__main__')

    mock_news_collect_service.collect_news_simple.assert_called_once()