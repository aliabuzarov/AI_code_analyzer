"""
Tests for prompt building and parsing logic.
"""
from django.test import TestCase
from explainers.llm_client import build_prompt, parse_llm_response


class PromptTestCase(TestCase):
    """Test cases for prompt building and parsing."""
    
    def test_build_prompt_includes_language(self):
        """Test that prompt includes the selected language."""
        prompt = build_prompt('python', 'print("hello")')
        self.assertIn('python', prompt.lower())
        self.assertIn('print("hello")', prompt)
    
    def test_build_prompt_includes_code(self):
        """Test that prompt includes the user's code."""
        code = 'def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)'
        prompt = build_prompt('python', code)
        self.assertIn(code, prompt)
    
    def test_build_prompt_includes_markers(self):
        """Test that prompt includes section markers."""
        prompt = build_prompt('python', 'x = 1')
        self.assertIn('### Explanation', prompt)
        self.assertIn('### Errors', prompt)
        self.assertIn('### Improved Code', prompt)
    
    def test_parse_llm_response_with_markers(self):
        """Test parsing LLM response with proper markers."""
        response = """### Explanation
This code prints hello world.

### Errors
None

### Improved Code
print("Hello, World!")
"""
        result = parse_llm_response(response)
        self.assertIn('explanation', result)
        self.assertIn('errors', result)
        self.assertIn('improved_code', result)
        self.assertIn('prints hello', result['explanation'].lower())
        self.assertIn('print("Hello', result['improved_code'])
    
    def test_parse_llm_response_missing_markers(self):
        """Test parsing LLM response without markers (graceful fallback)."""
        response = "This is just plain text without markers."
        result = parse_llm_response(response)
        self.assertIn('explanation', result)
        self.assertIn('errors', result)
        self.assertIn('improved_code', result)
        # Should have fallback values
        self.assertIsInstance(result['explanation'], str)
        self.assertIsInstance(result['errors'], str)
        self.assertIsInstance(result['improved_code'], str)
    
    def test_parse_llm_response_partial_markers(self):
        """Test parsing LLM response with some markers missing."""
        response = """### Explanation
This code does something.

### Errors
No errors found.
"""
        result = parse_llm_response(response)
        self.assertIn('explanation', result)
        self.assertIn('errors', result)
        self.assertIn('improved_code', result)
        self.assertIn('does something', result['explanation'].lower())
        self.assertIn('No errors', result['errors'])

