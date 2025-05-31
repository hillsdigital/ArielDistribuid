from django import forms
from django.contrib.auth.models import User

from ventas.models import Producto
from .models import Empleado

class CargarArchivoForm(forms.Form):
    archivo = forms.FileField()

class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'foto', 'categoria', 'precio_unidad', 'precio_bulto', 'cantidad_por_bulto']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        readonly_fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'precio_unidad', 'precio_bulto', 'cantidad_por_bulto']
        for field in readonly_fields:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True

class EmpleadoForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Empleado
        fields = ['es_admin']

    def save(self, commit=True):
        empleado = super().save(commit=False)
        if not empleado.pk:
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                email=self.cleaned_data['email']
            )
            empleado.user = user
        else:
            user = empleado.user
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            user.email = self.cleaned_data['email']
            user.save()
        if commit:
            empleado.save()
        return empleado