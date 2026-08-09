import json
import logging
from django.http import HttpResponse

logger = logging.getLogger(__name__)

# Paths that are NEVER blocked even in maintenance mode
EXEMPT_PREFIXES = (
    '/master/',      # dashboard master control endpoints (no /api prefix on cPanel)
    '/api/master/',  # same endpoints with /api prefix (local dev)
    '/dashboard/',   # the dashboard UI itself
    '/admin/',       # django admin
    '/static/',
    '/media/',
)


class MaintenanceModeMiddleware:
    """
    Checks the ServerConfig.api_enabled flag before every API request.
    If the flag is False, returns a 503 JSON response immediately.
    The /dashboard/ and /api/admin/ paths are always exempt so the
    admin can always reach the control panel to turn the API back on.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Allow exempt paths through unconditionally
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # Check maintenance mode for ALL paths not already exempted above.
        # On cPanel, Passenger strips the /api prefix before Django sees the request,
        # so paths arrive as /jobs/, /auth/google etc. — not /api/jobs/ etc.
        # We check everything and only exempt the prefixes listed above.
        try:
            from api.models import ServerConfig
            config = ServerConfig.get_config()
            if not config.api_enabled:
                body = json.dumps({
                    "error": "maintenance_mode",
                    "message": config.maintenance_message,
                    "status": 503
                })
                return HttpResponse(
                    body,
                    content_type='application/json',
                    status=503
                )
        except Exception as e:
            # If DB isn't ready yet (first migration etc.) just pass through
            logger.warning(f"MaintenanceModeMiddleware: could not read ServerConfig — {e}")

        return self.get_response(request)
