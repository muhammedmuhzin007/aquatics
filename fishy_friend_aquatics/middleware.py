from django.http import JsonResponse
from django.conf import settings


class AjaxLoginRedirectMiddleware:
    """Convert login redirects into JSON 401 responses for AJAX requests.

    When `@login_required` or other auth checks redirect to the login page for
    unauthenticated users, AJAX clients expect JSON. This middleware watches for
    redirect responses that point to the login URL and, when the request has
    `X-Requested-With: XMLHttpRequest`, returns a JSON 401 response instead.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        try:
            is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
            if is_ajax and response.status_code in (301, 302):
                location = response.get('Location', '')
                # If the redirect targets the login page (contains LOGIN_URL or '/login')
                login_url = getattr(settings, 'LOGIN_URL', 'login')
                if login_url and (login_url in location or '/login' in location):
                    return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        except Exception:
            # Fail open: do not interfere with non-related errors
            pass
        return response
