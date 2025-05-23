"""
Unit tests for the classifier processor module.
"""

from unittest.mock import Mock, patch

import pytest
from jinja2 import Template

from models import Classification
from processors.classifier_processor import get_llm_classification


def test_get_llm_classification_success() -> None:
    """Test successful LLM classification."""
    # Mock the OpenAI client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        '{"score": 2, "explanation": "Test explanation", "key_phrases": ["grace", "works"]}'
    )
    mock_client.chat.completions.create.return_value = mock_response

    # Create a simple template
    template = Template("Content: {{ content }}")

    # Test data
    text_content = "This is test content about grace and works"
    metadata = {"title": "Test Talk", "speaker": "Test Speaker", "year": "2024", "month": "04"}

    result = get_llm_classification(text_content, metadata, template, mock_client, "test-model")

    assert isinstance(result, Classification)
    assert result.score == 2
    assert result.explanation == "Test explanation"
    assert result.key_phrases == ["grace", "works"]
    assert result.model_used == "test-model"


def test_get_llm_classification_json_error() -> None:
    """Test handling of JSON parsing errors."""
    # Mock the OpenAI client with invalid JSON response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "invalid json response"
    mock_client.chat.completions.create.return_value = mock_response

    template = Template("Content: {{ content }}")
    text_content = "Test content"
    metadata = {"title": "Test Talk"}

    result = get_llm_classification(text_content, metadata, template, mock_client, "test-model")

    assert isinstance(result, Classification)
    assert result.score == 0
    assert "Error parsing LLM response" in result.explanation
    assert result.key_phrases == ["Error in classification"]
    assert result.model_used == "test-model"


def test_get_llm_classification_api_error() -> None:
    """Test handling of API errors."""
    # Mock the OpenAI client to raise an exception
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    template = Template("Content: {{ content }}")
    text_content = "Test content"
    metadata = {"title": "Test Talk"}

    result = get_llm_classification(text_content, metadata, template, mock_client, "test-model")

    assert isinstance(result, Classification)
    assert result.score == 0
    assert "Error in classification: API Error" in result.explanation
    assert result.key_phrases == ["Error in classification"]
    assert result.model_used == "test-model"


def test_get_llm_classification_missing_fields() -> None:
    """Test handling of response with missing required fields."""
    # Mock the OpenAI client with incomplete response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"score": 1}'  # Missing explanation and key_phrases
    mock_client.chat.completions.create.return_value = mock_response

    template = Template("Content: {{ content }}")
    text_content = "Test content"
    metadata = {"title": "Test Talk"}

    result = get_llm_classification(text_content, metadata, template, mock_client, "test-model")

    assert isinstance(result, Classification)
    assert result.score == 0
    assert "Error parsing LLM response" in result.explanation
    assert result.key_phrases == ["Error in classification"]


def test_get_llm_classification_invalid_score() -> None:
    """Test handling of invalid score values."""
    # Mock the OpenAI client with invalid score
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        '{"score": 5, "explanation": "Test", "key_phrases": ["test"]}'  # Score out of range
    )
    mock_client.chat.completions.create.return_value = mock_response

    template = Template("Content: {{ content }}")
    text_content = "Test content"
    metadata = {"title": "Test Talk"}

    result = get_llm_classification(text_content, metadata, template, mock_client, "test-model")

    assert isinstance(result, Classification)
    assert result.score == 0
    assert "Error parsing LLM response" in result.explanation


def test_get_llm_classification_string_key_phrases() -> None:
    """Test handling of key_phrases as string instead of list."""
    # Mock the OpenAI client with string key_phrases
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        '{"score": 1, "explanation": "Test", "key_phrases": "grace, works"}'
    )
    mock_client.chat.completions.create.return_value = mock_response

    template = Template("Content: {{ content }}")
    text_content = "Test content"
    metadata = {"title": "Test Talk"}

    result = get_llm_classification(text_content, metadata, template, mock_client, "test-model")

    assert isinstance(result, Classification)
    assert result.score == 1
    assert result.key_phrases == ["grace, works"]  # String converted to single-item list
