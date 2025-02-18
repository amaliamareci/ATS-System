from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('__reload__/', include('django_browser_reload.urls')),
    path('', include('core.urls')),  # Keep core URLs last
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 