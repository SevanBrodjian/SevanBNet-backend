from django.conf import settings


def client_ip(request):
    """The visitor's IP address, for login throttling and QR scan logs.

    On Railway every request arrives through its edge proxy, which sets X-Real-IP to
    the address it received the request from. Locally there is no proxy.
    """
    if settings.ON_RAILWAY:
        real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
        if real_ip:
            return real_ip
        # The leftmost X-Forwarded-For entries are client-supplied; the proxy appends last.
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")
