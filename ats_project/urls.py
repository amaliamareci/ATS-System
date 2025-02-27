"""
URL configuration for ats_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.static import serve
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__reload__/', include('django_browser_reload.urls')),
    path('', include('core.urls')),
    path('candidates/', include('candidates.urls')),
    path('positions/', include('positions.urls')),
    path('clients/', include('clients.urls')),
    path('meetings/', include('meetings.urls')),
    path('recruiters/', include('recruiters.urls')),
    path('recruitment/', include('recruitment.urls', namespace='recruitment')),
    path('communications/', include('communications.urls')),
    path('assessments/', include('assessments.urls', namespace='assessments')),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Secure file serving in production
    urlpatterns += [
        path('media/<path:path>', login_required(serve), {'document_root': settings.MEDIA_ROOT}),
    ]
