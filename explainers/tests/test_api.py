"""
Tests for API endpoints.
"""
import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse


class ExplainAPITestCase(TestCase):
    """Test cases for the explain API endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.url = '/api/explain/'
    
    def test_explain_api_valid_request(self):
        """Test that a valid request returns expected JSON structure."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.json.return_value = {
            'text': """### Explanation
This code calculates the sum of numbers from 1 to n.

### Errors
- No input validation for negative numbers

### Improved Code
def sum_numbers(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    return sum(range(1, n + 1))
"""
        }
        mock_response.raise_for_status = Mock()
        
        with patch('explainers.llm_client.requests.post', return_value=mock_response):
            with patch('explainers.llm_client.settings.LLM_API_URL', 'http://test-api.com'):
                with patch('explainers.llm_client.settings.LLM_API_KEY', 'test-key'):
                    response = self.client.post(
                        self.url,
                        data=json.dumps({
                            'language': 'python',
                            'code': 'def sum(n): return sum(range(1, n+1))'
                        }),
                        content_type='application/json'
                    )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('explanation', data)
        self.assertIn('errors', data)
        self.assertIn('improved_code', data)
    
    def test_explain_api_invalid_json(self):
        """Test that invalid JSON returns 400."""
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_explain_api_missing_language(self):
        """Test that missing language returns 400."""
        response = self.client.post(
            self.url,
            data=json.dumps({'code': 'print("hello")'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_explain_api_invalid_language(self):
        """Test that invalid language returns 400."""
        response = self.client.post(
            self.url,
            data=json.dumps({'language': 'javascript', 'code': 'console.log("hello")'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_explain_api_empty_code(self):
        """Test that empty code returns 400."""
        response = self.client.post(
            self.url,
            data=json.dumps({'language': 'python', 'code': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_explain_api_oversized_code(self):
        """Test that oversized code returns 400."""
        large_code = 'x = 1\n' * 600  # Exceeds 500 lines
        response = self.client.post(
            self.url,
            data=json.dumps({'language': 'python', 'code': large_code}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_explain_api_llm_failure(self):
        """Test that LLM API failure returns 500."""
        with patch('explainers.llm_client.call_llm_api', return_value=(False, {}, 'API error')):
            response = self.client.post(
                self.url,
                data=json.dumps({
                    'language': 'python',
                    'code': 'print("hello")'
                }),
                content_type='application/json'
            )
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)

