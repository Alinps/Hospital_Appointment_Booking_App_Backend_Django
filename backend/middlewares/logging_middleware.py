import time
import logging

logger = logging.getLogger("recipe_app")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        start_time = time.time()

        # Request info
        method = request.method
        path = request.path
        user = request.user if request.user.is_authenticated else "Anonymous"
        ip = self.get_ip(request)

        logger.info(f"REQUEST → {method} {path} | User: {user} | IP: {ip}")

        response = self.get_response(request)

        # Response info
        duration = time.time() - start_time

        logger.info(
            f"RESPONSE ← {method} {path} | Status: {response.status_code} | Time: {duration:.2f}s"
        )

        return response

    def get_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0]
        return request.META.get("REMOTE_ADDR")