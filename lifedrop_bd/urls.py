"""
URL configuration for lifedrop_bd project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('donors/', include('donors.urls', namespace='donors')),
    path('requests/', include('blood_requests.urls', namespace='blood_requests')),
    path('donations/', include('donations.urls', namespace='donations')),
    path('hospitals/', include('hospitals.urls', namespace='hospitals')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
