from django.core.management.base import BaseCommand
from ventas.models import BlockedIP
import os

class Command(BaseCommand):
    help = 'Genera el archivo de configuración de Nginx con las IPs bloqueadas'

    def handle(self, *args, **kwargs):
        blocked_ips = BlockedIP.objects.filter(permanently_blocked=True)
        
        # Ruta donde se almacenará el archivo
        nginx_config_path = '/etc/nginx/blocked_ips.conf'

        # Si no hay IPs bloqueadas, asegurarse de que el archivo esté vacío
        if not blocked_ips.exists():
            with open(nginx_config_path, 'w') as f:
                f.write("")  # Crear archivo vacío

        try:
            with open(nginx_config_path, 'w') as f:
                for blocked_ip in blocked_ips:
                    f.write(f"deny {blocked_ip.ip_address};\n")
            self.stdout.write(self.style.SUCCESS(f"Archivo de IPs bloqueadas generado en {nginx_config_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al generar el archivo: {str(e)}"))
