from django.urls import path
from . import views

urlpatterns = [
    path("pipelines/", views.teste, name='teste')
]