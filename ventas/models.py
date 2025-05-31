import os
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)  # Se puede mantener por ahora
    codigo = models.CharField(max_length=50, unique=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)  # Nuevo campo
    foto = models.ImageField(upload_to='productos/', blank=True, null=True)
    precio_unidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Precio por unidad
    precio_bulto = models.DecimalField(max_digits=10, decimal_places=2, default=0)   # Precio por bulto
    cantidad_por_bulto = models.PositiveIntegerField(default=1)  # Nueva columna: cuántas unidades trae el bulto

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def delete(self, *args, **kwargs):
        if self.foto and os.path.isfile(self.foto.path):
            os.remove(self.foto.path)
        super().delete(*args, **kwargs)

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    es_admin = models.BooleanField(default=False)  # Puedes marcar aquí si es admin

    def __str__(self):
        return self.user.username
    

class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    attempts = models.IntegerField(default=0)
    permanently_blocked = models.BooleanField(default=False)

    def increment_attempt(self):
        """Incrementa el contador de intentos fallidos."""
        self.attempts += 1
        self.save()

    def reset_attempts(self):
        """Restablece los intentos de la IP a 0."""
        self.attempts = 0
        self.save()

    def is_blocked(self):
        """Devuelve True si la IP debe ser bloqueada permanentemente."""
        return self.permanently_blocked

    def block_permanently(self):
        """Marca la IP como permanentemente bloqueada."""
        self.permanently_blocked = True
        self.save()

    def __str__(self):
        return f"{self.ip_address} - Attempts: {self.attempts} - Blocked: {self.permanently_blocked}"
