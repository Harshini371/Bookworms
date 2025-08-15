from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('iam.urls')), 
    path('api/', include('books.urls'))  # adjust if your app urls are elsewhere
]