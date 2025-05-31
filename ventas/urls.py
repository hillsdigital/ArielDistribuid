from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    ProductoCreateView,
    ProductoUpdateView,
    ProductoListView,
    HomePageView,
)

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('producto/create/', ProductoCreateView.as_view(), name='producto_create'),
    path('producto/<int:pk>/update/', ProductoUpdateView.as_view(), name='producto_update'),
    path('producto/<int:pk>/delete/', views.ProductoDeleteView.as_view(), name='producto_delete'),
    path('cargar/', views.cargar_archivo, name='cargar_archivo'),
    path('logout/', views.logout_view, name='logout'),
    path('acceso-privado-2024/', views.login_view, name='login'),  # URL oculta para login
    path('empleados/', views.empleado_list, name='empleado_list'),
    path('empleados/create/', views.empleado_create, name='empleado_create'),
    path('empleados/<int:pk>/update/', views.empleado_update, name='empleado_update'),
    path('empleados/<int:pk>/delete/', views.empleado_delete, name='empleado_delete'),
    path('empleados/<int:pk>/logout/', views.empleado_logout, name='empleado_logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)