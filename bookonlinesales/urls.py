from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('iam.urls')),  # adjust if your app urls are elsewhere
    
    
]