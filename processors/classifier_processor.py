"""
Classification processing functions for the Conference Talk Grace-Works Classifier.

This module handles the LLM classification logic.
"""

import json
import os
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template
from openai import OpenAI

from models import Classification, ProcessingResult, TalkMetadata


def get_llm_classification(
    text_content: str,
    metadata: Dict[str, Any],
    template: Template,
    client: OpenAI,
    model: str = "o4-mini-2025-04-16",
) -> Classification:
    """
    Uses the Jinja template to generate a prompt for the LLM and processes its response.
    Makes an actual API call to OpenAI.

    Args:
        text_content: The text content to classify
        metadata: Dictionary containing talk metadata
        template: Jinja2 template for generating prompts
        client: OpenAI client instance
        model: Model name to use for classification

    Returns:
        Classification object with score, explanation, and key phrases
    """
    # Generate the prompt using the template
    prompt = template.render(
        title=metadata.get("title", "Unknown Title"),
        speaker=metadata.get("speaker", "Unknown Speaker"),
        conference=metadata.get("conference", "Unknown Conference"),
        date=f"{metadata.get('year', '')}-{metadata.get('month', '')}",
        content=text_content,
    )

    print(f"Generated prompt for talk: {metadata.get('title', 'Unknown Title')}")

    try:
        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing religious talks and determining their theological emphasis. You will output a JSON object with the fields 'score', 'explanation', and 'key_phrases'.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent classifications
            response_format={"type": "json_object"},  # Enable JSON mode
        )

        # Extract the response content
        response_text = response.choices[0].message.content

        if response_text is None:
            print(f"Error: Received empty response from OpenAI API")
            return Classification(
                score=0,
                explanation="Error: Empty response from API",
                key_phrases=["Error in classification"],
                model_used=model,
            )

        # Parse the JSON response
        try:
            classification_data = json.loads(response_text)

            # Validate the response format
            if not all(
                key in classification_data for key in ["score", "explanation", "key_phrases"]
            ):
                print(f"Error parsing LLM response: Response missing required fields")
                print(f"Raw response: {response_text}")
                return Classification(
                    score=0,
                    explanation="Error parsing LLM response",
                    key_phrases=["Error in classification"],
                    model_used=model,
                )

            if (
                not isinstance(classification_data["score"], int)
                or not -3 <= classification_data["score"] <= 3
            ):
                print(f"Error parsing LLM response: Score must be an integer between -3 and 3")
                print(f"Raw response: {response_text}")
                return Classification(
                    score=0,
                    explanation="Error parsing LLM response",
                    key_phrases=["Error in classification"],
                    model_used=model,
                )

            # Ensure key_phrases is a list
            key_phrases = classification_data["key_phrases"]
            if isinstance(key_phrases, str):
                key_phrases = [key_phrases]
            elif not isinstance(key_phrases, list):
                key_phrases = list(key_phrases)

            return Classification(
                score=classification_data["score"],
                explanation=classification_data["explanation"],
                key_phrases=key_phrases,
                model_used=model,
            )

        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Raw response: {response_text}")
            return Classification(
                score=0,
                explanation="Error parsing LLM response",
                key_phrases=["Error in classification"],
                model_used=model,
            )

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return Classification(
            score=0,
            explanation=f"Error in classification: {str(e)}",
            key_phrases=["Error in classification"],
            model_used=model,
        )
