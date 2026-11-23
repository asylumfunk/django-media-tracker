"""Routes for the admin site and the API health check."""

from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    """Report that the API can serve requests."""
    return Response({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health, name='health'),
]
