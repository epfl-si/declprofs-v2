"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path
from .services import tinymce_upload_image

def forbidden(request):
    return render(request, "403.html", status=403)


urlpatterns = [
    path("", include("activities.urls")),
    path("users/", include("users.urls")),
    path("notifications/", include("notifications.urls")),
    path("campaign/", include("campaigns.urls")),
    path("documentation/", include("documentation.urls")),
    path("logs/", include("auditlogs.urls")),
    path('admin/', admin.site.urls),
    path("", include("django_epfl_entra_id.urls")),
    path("auth/", include("mozilla_django_oidc.urls")),
    path("forbidden/", forbidden, name="forbidden"),
    path("tinymce/upload-image/", tinymce_upload_image, name="tinymce_upload_image"),
    path("tinymce/", include("tinymce.urls")),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
