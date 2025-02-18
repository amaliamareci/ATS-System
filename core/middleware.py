import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse

class RequireLoginMiddleware:
    """Middleware to require login for all pages except those explicitly excluded."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Compile URL patterns
        self.required = tuple(re.compile(url) for url in settings.LOGIN_REQUIRED_URLS)
        self.exceptions = tuple(re.compile(url) for url in settings.LOGIN_REQUIRED_URLS_EXCEPTIONS)

    def __call__(self, request):
        # Check if the path matches any exception patterns
        path = request.path_info.lstrip('/')
        
        # Allow access to login-related URLs
        if any(pattern.match(path) for pattern in self.exceptions):
            return self.get_response(request)
            
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required',
                    'login_url': f"{settings.LOGIN_URL}?next={request.path}"
                }, status=401)
            
            # Store the current path for redirect after login
            next_url = request.path
            login_url = settings.LOGIN_URL
            
            # Add 'next' parameter if we have a path to return to
            if next_url and next_url != settings.LOGIN_URL:
                login_url = f"{login_url}?next={next_url}"
                
            return redirect(login_url)
        
        return self.get_response(request) 