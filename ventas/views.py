import os

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.core.files.storage import default_storage
from django.views.generic import  UpdateView, ListView
from django.views.generic.edit import CreateView, DeleteView
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import redirect
from ventas.forms import CargarArchivoForm, ProductoForm, EmpleadoForm
from .models import Producto, Empleado
import pandas as pd

# Create your views here.

HEADER_MAP_PRODUCTO = {
    'CODIGO': ['CODIGO', 'CÓDIGO', 'Código', 'COD'],
    'PRODUCTO': ['PRODUCTO', 'DESCRIPCION', 'DESCRIPCIÓN', 'Producto'],
    'PRECIOU': ['PRECIOU', 'PRECIO U', 'Precio Unidad', 'PrecioU', 'Precio por unidad', 'PRECIO UNIDAD', 'PrecioU'],
    'PRECIOB': ['PRECIOB', 'PRECIO B', 'Precio Bulto', 'PrecioB', 'Precio por bulto', 'PRECIO BULTO', 'PrecioB'],
    'CATEGORIA': ['CATEGORIA', 'Categoría', 'Categoria', 'Rubro', 'RUBRO']
}

def normalize_header(header, header_map):
    """Normaliza los encabezados a un formato estándar."""
    for key, variations in header_map.items():
        if str(header).strip() in variations:
            return key
    return header

def detectar_fila_encabezado(df):
    """Detecta la fila donde están los encabezados en el archivo."""
    for i in range(len(df)):
        if any(df.iloc[i].str.contains('|'.join(HEADER_MAP_PRODUCTO.keys()), na=False, case=False)):
            return i
    raise ValueError("No se encontraron encabezados reconocibles en el archivo")

def process_excel(file_path):
    """Procesa el archivo Excel y organiza los datos si es necesario."""
    try:
        # Intenta leer el archivo con engine openpyxl explícitamente
        df = pd.read_excel(file_path, header=None, engine="openpyxl")
        print("Primeras filas del archivo leído:")
        print(df.head())

        # Detectar la fila donde están los encabezados
        fila_encabezado = detectar_fila_encabezado(df)
        print("Fila de encabezado detectada:", fila_encabezado)
        print("Encabezados detectados:", list(df.iloc[fila_encabezado]))

        df.columns = [normalize_header(col, HEADER_MAP_PRODUCTO) for col in df.iloc[fila_encabezado]]
        df = df[fila_encabezado + 1:]

        # Eliminar filas vacías
        df.dropna(how='all', inplace=True)

        print("Primeras filas después de limpiar:")
        print(df.head())

        return None, df

    except Exception as e:
        print("Error en process_excel:", str(e))
        return f"Ocurrió un error al procesar el archivo: {str(e)}", None

def almacenar_datos_en_modelo(df, proveedor):
    """
    Almacena los datos procesados en el modelo Producto y los asocia con el proveedor.
    """
    for _, row in df.iterrows():
        try:
            print(f"Procesando fila: {row.to_dict()}")  # Mensaje de depuración
            codigo = row.get('CODIGO', 'No disponible')
            producto, creado = Producto.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre': row.get('PRODUCTO', ''),
                    'descripcion': row.get('DESCRIPCION', ''),
                    'precio_unidad': row.get('PRECIOU', 0),
                    'precio_bulto': row.get('PRECIOB', 0),
                    'categoria': row.get('CATEGORIA', ''),
                }
            )
            if creado:
                print(f'Producto creado: {codigo}')
            else:
                print(f'Producto actualizado: {codigo}')

            # Asociar el producto con el proveedor seleccionado
            producto.proveedores.add(proveedor)
            print(f'Producto {codigo} asociado con el proveedor {proveedor.nombre}')

        except Exception as e:
            print(f"Error al almacenar el producto {row.get('CODIGO', 'No disponible')}: {str(e)}")


def es_admin_o_superuser(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return hasattr(user, 'empleado') and user.empleado.es_admin
    except Empleado.DoesNotExist:
        return False

def solo_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(es_admin_o_superuser)
def cargar_archivo(request):
    if request.method == 'POST':
        form = CargarArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            proveedor = form.cleaned_data.get('proveedor')  # Asegúrate de obtener el proveedor si el form lo tiene
            archivo_path = default_storage.save(archivo.name, archivo)
            archivo_full_path = default_storage.path(archivo_path)

            error, df = process_excel(archivo_full_path)

            print("Archivo recibido:", archivo_full_path)
            if df is not None:
                print(df.head())
            else:
                print("El DataFrame es None")

            if df is None or df.empty:
                os.remove(archivo_full_path)
                return render(request, 'cargar_archivo.html', {'form': form})

            if proveedor:
                almacenar_datos_en_modelo(df, proveedor)
            else:
                almacenar_datos_en_modelo(df, None)

            os.remove(archivo_full_path)

            return render(request, 'cargar_archivo.html', {'form': form})
    else:
        form = CargarArchivoForm()

    return render(request, 'cargar_archivo.html', {'form': form})


# @method_decorator(superuser_required, name='dispatch')
@method_decorator(user_passes_test(es_admin_o_superuser), name='dispatch')
class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto_list')



# @method_decorator(superuser_required, name='dispatch')
@method_decorator(user_passes_test(es_admin_o_superuser), name='dispatch')
class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto_list')

    def form_valid(self, form):
        producto = form.save(commit=False)
        if 'foto' in form.changed_data:  # Verifica si se ha cambiado la foto
            old_foto = self.get_object().foto
            if old_foto:
                if os.path.isfile(old_foto.path):
                    os.remove(old_foto.path)  # Elimina la foto anterior del sistema de archivos
        producto.save()
        return super().form_valid(form)
# @method_decorator(superuser_required, name='dispatch')
@method_decorator(user_passes_test(es_admin_o_superuser), name='dispatch')
class ProductoListView(ListView):
    model = Producto
    template_name = 'producto_list.html'
    context_object_name = 'productos'

class HomePageView(ListView):
    model = Producto
    template_name = 'home.html'
    context_object_name = 'productos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener categorías únicas, ignorando vacíos/nulos
        categorias = (
            Producto.objects.exclude(categoria__isnull=True)
            .exclude(categoria__exact="")
            .values_list('categoria', flat=True)
            .distinct()
        )
        context['categorias'] = categorias
        return context

def logout_view(request):
    logout(request)
    return redirect('home')

def login_view(request):
    # Simple login view (puedes personalizarlo)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'login.html')

@user_passes_test(solo_superuser)
def empleado_list(request):
    empleados = Empleado.objects.select_related('user').all()
    return render(request, 'empleado_list.html', {'empleados': empleados})

@user_passes_test(solo_superuser)
def empleado_create(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('empleado_list')
    else:
        form = EmpleadoForm()
    return render(request, 'empleado_form.html', {'form': form})

@user_passes_test(solo_superuser)
def empleado_update(request, pk):
    empleado = Empleado.objects.get(pk=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect('empleado_list')
    else:
        form = EmpleadoForm(instance=empleado, initial={
            'username': empleado.user.username,
            'email': empleado.user.email,
        })
    return render(request, 'empleado_form.html', {'form': form, 'empleado': empleado})

@user_passes_test(solo_superuser)
def empleado_delete(request, pk):
    empleado = Empleado.objects.get(pk=pk)
    if request.method == 'POST':
        empleado.user.delete()
        empleado.delete()
        return redirect('empleado_list')
    return render(request, 'empleado_confirm_delete.html', {'empleado': empleado})

@user_passes_test(solo_superuser)
def empleado_logout(request, pk):
    # Forzar logout de un usuario (requiere sesión backend custom, aquí solo ejemplo)
    # En la práctica, puedes desactivar el usuario:
    empleado = Empleado.objects.get(pk=pk)
    empleado.user.is_active = False
    empleado.user.save()
    return redirect('empleado_list')

@method_decorator(user_passes_test(es_admin_o_superuser), name='dispatch')
class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'producto_confirm_delete.html'
    success_url = reverse_lazy('producto_list')