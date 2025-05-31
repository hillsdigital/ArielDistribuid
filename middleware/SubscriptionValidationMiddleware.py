# import requests
# from django.shortcuts import redirect
# from django.conf import settings
# from django.contrib.auth import logout
# from django.utils import timezone

# class SubscriptionValidationMiddleware:
#     """
#     Middleware para verificar el estado de la suscripción del usuario
#     antes de permitir su acceso.
#     """

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Evitar validación en login y acceso denegado
#         if request.path in ['/login/', '/access-denied/']:
#             return self.get_response(request)

#         # Validar solo usuarios autenticados
#         if request.user.is_authenticated:
#             # Verificar si ya se ha comprobado la suscripción en la sesión
#             if 'subscription_status_checked' not in request.session:
#                 subscription_api_url = f"{settings.SUBSCRIPTION_MANAGER_API_URL}/subscription/status/"

#                 try:
#                     # Consultar el estado de la suscripción de este usuario
#                     response = requests.get(
#                         subscription_api_url,
#                         params={"user_id": request.user.id},
#                         timeout=5
#                     )

#                     # Verificamos si la respuesta es válida (200 OK)
#                     if response.status_code == 200:
#                         subscription_data = response.json()

#                         # Verificamos si la suscripción está activa
#                         if not subscription_data.get("is_active", False):
#                             # Si la suscripción no está activa, cerramos sesión
#                             logout(request)
#                             request.session.flush()  # Limpiamos la sesión
#                             return redirect("login")  # Redirigimos a la página de login

#                         # Si la suscripción está activa, marcamos que ya se validó
#                         request.session['subscription_status_checked'] = True
#                     else:
#                         # Si la respuesta de la API no es exitosa, redirigimos al login
#                         print(f"Error al consultar la API de suscripción: Código de estado {response.status_code}")
#                         return redirect("login")

#                 except requests.RequestException as e:
#                     # Si hay un error de conexión, también redirigimos
#                     print(f"Error al consultar la API de suscripción: {e}")
#                     return redirect("login")

#         # Continuamos con la respuesta original si no hay problemas
#         response = self.get_response(request)
#         return response
