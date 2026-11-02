import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.models import TokenUser

from apps.profile.services.profile_service import get_or_sync_profile

# class AuthenticatedUser:
#     def __init__(self, payload):
#         self.id = payload.get("user_id")
#         self.pk = self.id  # Add this
#         self.email = payload.get("email", "")
#         self._is_authenticated = True
#         self.is_active = True
#         self.is_staff = False
#         self.is_superuser = False
#         self.backend = 'django.contrib.auth.backends.ModelBackend'  # Add this
#
#     @property
#     def is_authenticated(self):
#         return self._is_authenticated
#
#     def __str__(self):
#         return self.email or f"user-{self.id}"
#
#     def has_perm(self, perm, obj=None):
#         return True
#
#     def has_module_perms(self, app_label):
#         return True
#
# class AuthMiddleware:
#     """
#     Update your AuthMiddleware class to attach a fake user object (not the real Django user) using the JWT payload.
#     This enables request.user.id and request.user.is_authenticated to behave normally.
#     """
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         print("AuthMiddleware active")
#         auth_header = request.headers.get("Authorization", "")
#         token = auth_header.replace("Bearer ", "")
#
#         if token:
#             try:
#                 payload = jwt.decode(token, settings.AUTH_SECRET_KEY, algorithms=["HS256"])
#                 request.user = AuthenticatedUser(payload)
#                 print(f"User set in request: id={request.user.id}, authenticated={request.user.is_authenticated}")
#                 request.user_id = payload.get("user_id")
#
#                 request.user_info = payload
#                 print(f"user_info: {request.user_info}")
#             except jwt.ExpiredSignatureError:
#                 return JsonResponse({'error': 'Token expired'}, status=401)
#             except jwt.InvalidTokenError:
#                 return JsonResponse({'error': 'Invalid token'}, status=401)
#         else:
#             request.user = AnonymousUser()
#             print("AnonymousUser set in request")
#             request.user_id = None
#             request.user_info = {}
#
#         return self.get_response(request)

class JWTUser:
    def __init__(self, payload):
        self.id = payload.get("user_id")
        self.email = payload.get("email", "")
        self.is_active = True
        # self.is_staff = False
        # self.is_superuser = False
        self.is_staff = payload.get("is_staff", False)
        self.is_superuser = payload.get("is_superuser", False)
        self._is_authenticated = True
        self.pk = self.id
        self.backend = 'rest_framework.authentication.BaseAuthentication'

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def __str__(self):
        return self.email or f"user-{self.id}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None  # No authentication attempted

        token = auth_header[len('Bearer '):]

        try:
            payload = jwt.decode(token, settings.AUTH_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        user = JWTUser(payload)

        # === SYNC TRIGGER ===
        # Ensure the profile exists in our microservice DB before the view runs.
        # We pass the token so the service can make upstream requests.
        get_or_sync_profile(user, token)
        
        return (user, None)