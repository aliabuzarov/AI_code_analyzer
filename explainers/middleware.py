"""
Rate limiting middleware for API endpoints.
"""
import time
from django.http import JsonResponse
from django.conf import settings
from collections import defaultdict


# In-memory rate limiter (simple implementation)
# For production, consider using Redis or django-ratelimit
_rate_limit_store = defaultdict(list)


class RateLimitMiddleware:
    """
    Simple in-memory rate limiting middleware.
    
    Limits requests per IP address based on RATE_LIMIT_REQUESTS and RATE_LIMIT_WINDOW.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW
    
    def __call__(self, request):
        # Only rate limit API endpoints
        if request.path.startswith('/api/'):
            ip_address = self._get_client_ip(request)
            current_time = time.time()
            
            # Clean old entries outside the window
            _rate_limit_store[ip_address] = [
                timestamp for timestamp in _rate_limit_store[ip_address]
                if current_time - timestamp < self.window_seconds
            ]
            
            # Check if limit exceeded
            if len(_rate_limit_store[ip_address]) >= self.max_requests:
                return JsonResponse(
                    {'error': f'Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds // 60} minutes.'},
                    status=429
                )
            
            # Record this request
            _rate_limit_store[ip_address].append(current_time)
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

