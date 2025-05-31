from django.core.management.base import BaseCommand
from ventas.models import BlockedIP

class Command(BaseCommand):
    help = 'Lista las IPs bloqueadas permanentemente'

    def handle(self, *args, **kwargs):
        blocked_ips = BlockedIP.objects.filter(permanently_blocked=True)

        if not blocked_ips:
            self.stdout.write(self.style.SUCCESS('No hay IPs bloqueadas'))
        else:
            for blocked_ip in blocked_ips:
                self.stdout.write(f"IP: {blocked_ip.ip_address} | Intentos: {blocked_ip.attempts} | Bloqueada: {blocked_ip.permanently_blocked}")
