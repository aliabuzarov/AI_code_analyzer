"""
Views for the explainers app.
"""
import json
from typing import Tuple, Optional
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .llm_client import call_llm_api
from .serializers import ExplainRequestSerializer


def index(request):
    """Render the home page."""
    from django.shortcuts import render
    return render(request, 'explainers/index.html')


def validate_code_input(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate code input for size and content.
    
    Args:
        code: User's code string
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not code or not code.strip():
        return False, "Code cannot be empty"
    
    # Check length
    if len(code) > settings.MAX_CODE_LENGTH:
        return False, f"Code exceeds maximum length of {settings.MAX_CODE_LENGTH} characters"
    
    # Check line count
    lines = code.split('\n')
    if len(lines) > settings.MAX_LINES:
        return False, f"Code exceeds maximum of {settings.MAX_LINES} lines"
    
    # Sanitize: remove binary/null characters
    if '\x00' in code:
        return False, "Code contains invalid null characters"
    
    # Basic check for extremely long lines (potential DoS)
    max_line_length = 10000
    for line in lines:
        if len(line) > max_line_length:
            return False, f"Line exceeds maximum length of {max_line_length} characters"
    
    return True, None


@require_http_methods(["POST"])
def explain_api(request):
    """
    API endpoint to explain code.
    
    Accepts JSON: {"language": "python"|"cpp", "code": "<code>"}
    Returns JSON: {"explanation": "...", "errors": "...", "improved_code": "..."}
    """
    try:
        # Parse JSON request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Validate with serializer
        serializer = ExplainRequestSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        language = serializer.validated_data['language']
        code = serializer.validated_data['code']
        
        # Validate code input
        is_valid, error_msg = validate_code_input(code)
        if not is_valid:
            return JsonResponse({'error': error_msg}, status=400)
        
        # Call LLM API
        success, result, error_msg = call_llm_api(language, code)
        
        if not success:
            return JsonResponse({'error': error_msg or 'Failed to get explanation'}, status=500)
        
        return JsonResponse(result)
        
    except Exception as e:
        # In production, log this but don't expose internal errors
        if settings.DEBUG:
            return JsonResponse({'error': f'Internal error: {str(e)}'}, status=500)
        return JsonResponse({'error': 'An internal error occurred'}, status=500)

