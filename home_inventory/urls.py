"""
URL configuration for home_inventory project.

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
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.i18n import set_language
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from inventory import views

# Swagger schema view with token authentication
schema_view = get_schema_view(
   openapi.Info(
      title="Home Inventory API",
      default_version='v1',
      description="API documentation for Home Inventory Management System. "
                  "To use the API:\n"
                  "1. First, obtain a token by calling `POST /v1/api/auth/token/` with your username and password.\n"
                  "2. Copy the token from the response.\n"
                  "3. Click the 'Authorize' button (🔒) at the top of the page.\n"
                  "4. Enter: `Token <your_token>` (replace <your_token> with the actual token).\n"
                  "5. Click 'Authorize' and then 'Close'.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@homeinventory.local"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   patterns=[
      path('v1/api/', include('inventory.api_urls')),
   ],
)

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('i18n/setlang/', set_language, name='set_language'),
    path('', RedirectView.as_view(url='/v1/', permanent=False), name='root_redirect'),
    path('v1/', include([
        # Home page - cached internally (user-specific)
        path('', views.home, name='home'),
        # List pages
        path('locations/', views.location_list, name='location_list'),
        path('items/', views.item_list, name='item_list'),
        # Detail pages
        path('locations/<uuid:location_id>/', views.location_detail, name='location_detail'),
        path('items/<uuid:item_id>/', views.item_detail, name='item_detail'),
        path('room/<str:room_type>/', views.room_view, name='room_view'),
        path('search/', views.search, name='search'),
        path('notifications/', views.notification_list, name='notification_list'),
        path('notifications/<uuid:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
        path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
        path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
        path('api/', include('inventory.api_urls')),
    ])),
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass  # debug_toolbar not installed

