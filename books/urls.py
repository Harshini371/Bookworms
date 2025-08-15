from django.urls import path
from .views import AuthorView, AuthorListView

urlpatterns = [
    path('createauthor/', AuthorView.as_view(), name='author_create'),
    path('getauthors/', AuthorListView.as_view(), name='author_list')
]