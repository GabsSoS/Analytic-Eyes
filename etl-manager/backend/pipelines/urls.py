from django.urls import path
from . import views

urlpatterns = [
    path("pipelines/<int:pipeline_id>/", views.execute_pipeline, name='execute_pipeline')
]