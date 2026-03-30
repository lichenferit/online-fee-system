
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('feeapp.urls')),
    path('challan/', include('feeapp.urls')),
    path('accounts/login/', RedirectView.as_view(url='/clerk/login/', permanent=False)),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)