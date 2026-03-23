import time
from django.http import JsonResponse
from django.core.cache import cache

class GlobalRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.window = 60

    def __call__(self, request):
        identifier,limit = self.get_identifier_and_limit(request)

        key = f"rl:{identifier}"
        data = cache.get(key)

        now = time.time()

        if data is None:
            # First request
            cache.set(key,(1,now), timeout = self.window)
        else:
            count, start_time = data

            if now - start_time < self.window:
                if count >= limit:
                    return JsonResponse(
                        {"error":"Too many requests. Try again later,"},status=429
                    )
                cache.set(key, (count + 1,start_time), timeout=self.window)
            else:
                cache.set(key,(1,now), timeout=self.window)
        return self.get_response(request)
    
    def get_identifier_and_limit(self,request):
        # Authenticated user
        if request.user.is_authenticated:
            return f"user:{request.user.id}",100
        
                # Anonymous user → IP-based
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            ip = x_forwarded.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")

        return f"ip:{ip}", 30
        
