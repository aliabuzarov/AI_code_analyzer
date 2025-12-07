"""
LLM client for code explanation service.

This module handles communication with external LLM APIs and includes
prompt engineering logic to extract structured responses.
"""
import json
import re
import time
from typing import Dict, Optional, Tuple
import requests
from django.conf import settings


# Example prompt template with explicit markers for structured output
PROMPT_TEMPLATE = """You are an assistant that explains code for learners. Given the user code and language below, return three clearly separated sections delimited by the headers exactly as shown:

### Explanation
A short plain-language explanation (2–6 sentences) of what the code does, aimed at a beginner.

### Errors
A short bullet list of likely bugs, runtime errors, or edge cases. If none, write "None".

### Improved Code
A cleaned and (if needed) fixed version of the code. Keep it concise and idiomatic for the language. Include minimal inline comments if helpful.

User language: {language}
User code:

{code}

Example format:
### Explanation
This code calculates the factorial of a number using recursion.

### Errors
- No input validation; will crash on negative numbers
- Stack overflow risk for large numbers

### Improved Code
def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    return 1 if n <= 1 else n * factorial(n - 1)
"""


def build_prompt(language: str, code: str) -> str:
    """
    Build a prompt for the LLM with the given code and language.
    
    Args:
        language: Programming language ('python' or 'cpp')
        code: User's code snippet
        
    Returns:
        Formatted prompt string
    """
    return PROMPT_TEMPLATE.format(language=language, code=code)


def parse_serper_response(serper_data: Dict, language: str, code: str) -> str:
    """
    Parse Serper API search results and format as code explanation.
    
    Args:
        serper_data: Serper API response dictionary
        language: Programming language
        code: User's code snippet
        
    Returns:
        Formatted text with explanation, errors, and improved code sections
    """
    explanation_parts = []
    error_parts = []
    improved_code = code  # Start with original code
    
    # Extract organic results
    organic_results = serper_data.get('organic', [])
    answer_box = serper_data.get('answerBox', {})
    
    # Use answer box if available
    if answer_box:
        answer_text = answer_box.get('answer', '') or answer_box.get('snippet', '')
        if answer_text:
            explanation_parts.append(answer_text)
    
    # Extract snippets from top results
    for result in organic_results[:3]:
        snippet = result.get('snippet', '')
        title = result.get('title', '')
        if snippet:
            explanation_parts.append(f"{title}: {snippet}")
    
    # Build explanation
    explanation = "Based on search results:\n\n" + "\n\n".join(explanation_parts[:3])
    if not explanation_parts:
        explanation = f"Found {len(organic_results)} search results for {language} code. Review the code structure and common patterns."
    
    # Try to identify common errors from search results
    error_keywords = ['error', 'bug', 'issue', 'problem', 'exception', 'crash']
    for result in organic_results:
        snippet = result.get('snippet', '').lower()
        if any(keyword in snippet for keyword in error_keywords):
            error_parts.append(result.get('snippet', ''))
    
    errors = "\n- ".join(error_parts[:3]) if error_parts else "None identified from search results."
    if error_parts:
        errors = "- " + errors
    
    # Format as structured response
    formatted_response = f"""### Explanation
{explanation}

### Errors
{errors}

### Improved Code
{improved_code}
"""
    return formatted_response


def parse_llm_response(response_text: str) -> Dict[str, str]:
    """
    Parse LLM response text into structured sections.
    
    Uses regex to extract sections marked with ### headers.
    Falls back gracefully if markers are missing.
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Dictionary with keys: explanation, errors, improved_code
    """
    # Try to extract sections using markers
    explanation_match = re.search(r'###\s*Explanation\s*\n(.*?)(?=###|$)', response_text, re.DOTALL | re.IGNORECASE)
    errors_match = re.search(r'###\s*Errors?\s*\n(.*?)(?=###|$)', response_text, re.DOTALL | re.IGNORECASE)
    improved_match = re.search(r'###\s*Improved\s+Code\s*\n(.*?)(?=###|$)', response_text, re.DOTALL | re.IGNORECASE)
    
    explanation = explanation_match.group(1).strip() if explanation_match else "Explanation not available."
    errors = errors_match.group(1).strip() if errors_match else "Error analysis not available."
    improved_code = improved_match.group(1).strip() if improved_match else "# Improved code not available."
    
    return {
        'explanation': explanation,
        'errors': errors,
        'improved_code': improved_code
    }


def call_llm_api(language: str, code: str) -> Tuple[bool, Dict[str, str], Optional[str]]:
    """
    Call the external LLM API to get code explanation.
    
    This function is designed to work with generic REST APIs. To adapt it for
    a specific provider (e.g., OpenAI, Anthropic):
    
    1. Modify the request body structure in the 'data' variable
    2. Adjust headers if needed (some providers use different auth schemes)
    3. Update the response parsing if the API returns a different format
    
    Example for OpenAI:
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMPERATURE
        }
        headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
    
    Args:
        language: Programming language ('python' or 'cpp')
        code: User's code snippet
        
    Returns:
        Tuple of (success: bool, result: Dict[str, str], error_message: Optional[str])
    """
    if not settings.LLM_API_URL:
        return False, {}, "LLM_API_URL not configured"
    
    if not settings.LLM_API_KEY:
        return False, {}, "LLM_API_KEY not configured"
    
    prompt = build_prompt(language, code)
    
    # Detect provider and format request accordingly
    api_url_lower = settings.LLM_API_URL.lower()
    
    # Serper API (Google Search API) format
    if 'serper.dev' in api_url_lower or 'serper' in api_url_lower:
        # Build search queries for code explanation
        # Extract first few lines of code for search
        code_lines = code.split('\n')[:5]
        code_preview = ' '.join(code_lines[:3])
        search_query = f"{language} code explanation {code_preview}"
        
        data = {
            "q": search_query,
            "num": 5  # Get top 5 results
        }
        headers = {
            "X-API-KEY": settings.LLM_API_KEY,
            "Content-Type": "application/json"
        }
    # Google Gemini format
    elif 'generativelanguage.googleapis.com' in api_url_lower or 'gemini' in api_url_lower:
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": settings.LLM_TEMPERATURE,
                "maxOutputTokens": 2000,
            }
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.LLM_API_KEY
        }
    # OpenAI format
    elif 'openai' in api_url_lower:
        data = {
            "model": "gpt-4",  # or "gpt-3.5-turbo" - can be made configurable
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": 2000,
        }
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
    # Anthropic format
    elif 'anthropic' in api_url_lower:
        data = {
            "model": "claude-3-opus-20240229",  # or "claude-3-sonnet-20240229"
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "x-api-key": settings.LLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    # Generic format (default)
    else:
        data = {
            "prompt": prompt,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": 2000,
        }
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        }
    
    try:
        # Retry with exponential backoff for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    settings.LLM_API_URL,
                    json=data,
                    headers=headers,
                    timeout=30
                )
                
                # Handle rate limiting (429) with special retry logic
                if response.status_code == 429:
                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                        except ValueError:
                            wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                    else:
                        # Exponential backoff: 5s, 10s, 20s
                        wait_time = (2 ** attempt) * 5
                    
                    if attempt < max_retries - 1:
                        # Wait before retrying
                        time.sleep(wait_time)
                        continue
                    else:
                        # Last attempt failed
                        return False, {}, (
                            f"Rate limit exceeded. The API is temporarily unavailable. "
                            f"Please wait a few minutes before trying again. "
                            f"(Error: 429 Too Many Requests)"
                        )
                
                response.raise_for_status()
                
                # Parse response - adapt based on your provider's format
                response_data = response.json()
                
                # Serper API response format (search results)
                if 'serper.dev' in api_url_lower or 'serper' in api_url_lower:
                    # Parse Serper search results and format as code explanation
                    response_text = parse_serper_response(response_data, language, code)
                # Try common response formats
                elif isinstance(response_data, str):
                    response_text = response_data
                # Google Gemini format
                elif 'candidates' in response_data and len(response_data['candidates']) > 0:
                    candidate = response_data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if parts and len(parts) > 0 and 'text' in parts[0]:
                            response_text = parts[0]['text']
                        else:
                            response_text = json.dumps(response_data)
                    else:
                        response_text = json.dumps(response_data)
                # OpenAI-style format
                elif 'choices' in response_data and len(response_data['choices']) > 0:
                    response_text = response_data['choices'][0].get('message', {}).get('content', '')
                    if not response_text:
                        response_text = response_data['choices'][0].get('text', '')
                # Generic text/content fields
                elif 'text' in response_data:
                    response_text = response_data['text']
                elif 'content' in response_data:
                    response_text = response_data['content']
                else:
                    # Fallback: use entire response as string
                    response_text = json.dumps(response_data)
                
                parsed = parse_llm_response(response_text)
                return True, parsed, None
                
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    return False, {}, "Request timeout - LLM API did not respond in time. Please try again."
                # Wait before retrying timeout
                time.sleep(2 ** attempt)
                continue
            except requests.exceptions.HTTPError as e:
                # Handle other HTTP errors
                if e.response.status_code == 429:
                    # This shouldn't happen as we handle 429 above, but just in case
                    if attempt < max_retries - 1:
                        time.sleep((2 ** attempt) * 5)
                        continue
                    return False, {}, (
                        f"Rate limit exceeded. Please wait a few minutes before trying again. "
                        f"(Error: 429 Too Many Requests)"
                    )
                elif e.response.status_code == 401:
                    return False, {}, "Invalid API key. Please check your LLM_API_KEY in the .env file."
                elif e.response.status_code == 403:
                    return False, {}, "API access forbidden. Please check your API key permissions."
                elif e.response.status_code >= 500:
                    # Server errors - retry with backoff
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False, {}, f"LLM API server error ({e.response.status_code}). Please try again later."
                else:
                    # Other HTTP errors
                    return False, {}, f"LLM API error ({e.response.status_code}): {str(e)}"
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return False, {}, f"Network error: {str(e)}. Please check your internet connection and try again."
                # Wait before retrying network errors
                time.sleep(2 ** attempt)
                continue
                
    except Exception as e:
        return False, {}, f"Unexpected error: {str(e)}"
    
    return False, {}, "Failed to get response from LLM API"

