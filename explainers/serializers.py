"""
Simple validation for API requests (no DRF dependency).
"""
from typing import Dict, Optional


class ExplainRequestSerializer:
    """Simple serializer for explain API request validation."""
    
    def __init__(self, data: Dict):
        self.data = data
        self.errors = {}
    
    def is_valid(self) -> bool:
        """Validate the request data."""
        self.errors = {}
        
        # Validate language
        language = self.data.get('language')
        if not language:
            self.errors['language'] = 'Language is required'
        elif language not in ['python', 'cpp']:
            self.errors['language'] = 'Language must be "python" or "cpp"'
        
        # Validate code
        code = self.data.get('code')
        if code is None:
            self.errors['code'] = 'Code is required'
        elif not isinstance(code, str):
            self.errors['code'] = 'Code must be a string'
        elif not code.strip():
            self.errors['code'] = 'Code cannot be empty'
        
        return len(self.errors) == 0
    
    @property
    def validated_data(self) -> Dict:
        """Return validated data."""
        return {
            'language': self.data.get('language'),
            'code': self.data.get('code', '')
        }

