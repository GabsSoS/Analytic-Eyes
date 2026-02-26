from django.urls import path
from . import views

urlpatterns = [
    #execução de pipeline
    path("pipelines/<int:pipeline_id>/", views.execute_pipeline, name='execute_pipeline'),

    #litagem de pipes
    path("list-pipelines/", views.list_pipes, name='list_pipes')
]