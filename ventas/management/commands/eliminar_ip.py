from django.core.management.base import BaseCommand
from ventas.models import BlockedIP

class Command(BaseCommand):
    help = 'Elimina una IP bloqueada permanentemente por su dirección IP'

    def add_arguments(self, parser):
        # Agregar argumento para la IP a eliminar
        parser.add_argument('ip_address', type=str, help='Dirección IP a eliminar')

    def handle(self, *args, **kwargs):
        ip_address = kwargs['ip_address']
        
        # Buscar la IP bloqueada
        blocked_ip = BlockedIP.objects.filter(ip_address=ip_address).first()

        if blocked_ip:
            # Si existe, eliminar la IP
            blocked_ip.delete()
            self.stdout.write(self.style.SUCCESS(f'La IP {ip_address} ha sido eliminada de la lista de bloqueadas.'))
        else:
            self.stdout.write(self.style.ERROR(f'La IP {ip_address} no está bloqueada.'))
