from django.core.management.base import BaseCommand
from ventas.models import BlockedIP
import subprocess

class Command(BaseCommand):
    help = 'Bloquea una IP en el servidor y la registra en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument('ip', type=str)

    def handle(self, *args, **kwargs):
        ip = kwargs['ip']
        self.stdout.write(self.style.SUCCESS(f'Bloqueando la IP {ip}...'))

        # Buscar si la IP ya está bloqueada
        blocked_ip, created = BlockedIP.objects.get_or_create(ip_address=ip)

        if created:
            self.stdout.write(self.style.SUCCESS(f'IP {ip} registrada en la base de datos.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'IP {ip} ya está registrada en la base de datos.'))

        # Ejecutar el comando iptables para bloquear la IP
        try:
            subprocess.run(['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)

            # Marcar como bloqueada permanentemente en la base de datos
            blocked_ip.block_permanently()
            self.stdout.write(self.style.SUCCESS(f'IP {ip} bloqueada correctamente a nivel de servidor y en la base de datos.'))

        except subprocess.CalledProcessError:
            self.stdout.write(self.style.ERROR(f'Error al bloquear la IP {ip} a nivel de servidor.'))
