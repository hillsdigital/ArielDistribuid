from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import resolve, get_resolver, reverse
from django.conf import settings
from datetime import datetime
import logging
import re
from ventas.models import BlockedIP

logger = logging.getLogger(__name__)

SUSPICIOUS_PATHS = [
    r"/wp-includes", r"/xmlrpc.php", r"/admin", r"/solr", r"/login", r"\.php",
    r"\.env", r"\.git/", r"\.gitignore", r"\.htaccess", r"\.config", r"/config",
    r"/etc/passwd", r"/.ssh/", r"/.env", r"/composer\.json", r"/vendor/phpunit",
    r"\bselect\b.*\bfrom\b",  # Inyección SQL
    r"\b<script\b.*\b>\b",   # XSS
    r"union.*select.*from",  # SQL Injection
]

ALLOWED_PUBLIC_PATHS = [
    r"^/$",                          # raíz
    r"^/acceso-privado-2024/?$",     # login oculto
    r"^/favicon\.ico$",              # ícono
]

MAX_ATTEMPTS = 3


class BlockUnallowedRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        path = request.path

        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        blocked_ip = self.get_or_create_ip(ip)

        if blocked_ip.is_blocked():
            return HttpResponseForbidden("Acceso denegado: Tu IP está bloqueada.")

        if any(re.match(p, path) for p in ALLOWED_PUBLIC_PATHS):
            return self.get_response(request)

        if not self.is_allowed_url(path) or self.is_suspicious_path(path):
            self.log_unauthorized_attempt(request)
            blocked_ip.increment_attempt()
            if blocked_ip.attempts >= MAX_ATTEMPTS:
                blocked_ip.block_permanently()
                logger.warning(f"IP {ip} bloqueada permanentemente por múltiples intentos sospechosos.")
            return HttpResponseForbidden("Acceso denegado: Ruta no permitida o sospechosa.")

        if not request.user.is_authenticated:
            self.log_unauthorized_attempt(request)
            return HttpResponseRedirect(reverse('home'))

        return self.get_response(request)

    def get_or_create_ip(self, ip):
        obj, _ = BlockedIP.objects.get_or_create(ip_address=ip)
        return obj

    def is_allowed_url(self, path):
        resolver = get_resolver()
        allowed_urls = []
        for pattern in resolver.url_patterns:
            try:
                allowed_urls.append(pattern.pattern.regex.pattern)
            except AttributeError:
                continue
        return any(re.fullmatch(url, path) for url in allowed_urls)

    def is_suspicious_path(self, path):
        return any(re.search(pattern, path, re.IGNORECASE) for pattern in SUSPICIOUS_PATHS)

    def log_unauthorized_attempt(self, request):
        ip = self.get_client_ip(request)
        path = request.path
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.warning(f"{timestamp} - IP: {ip} - Intento de acceso no autorizado a: {path}")

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
