from django.urls import path
from . import views

urlpatterns = [
    #execução de pipeline
    path("pipelines/<int:pipeline_id>/", views.trigger_pipeline, name='execute_pipeline'),

    #litagem de pipes
    path("pipelines/", views.pipelines, name='list_pipelines'),
    #detalhes de uma pipe específica
    path("pipelines/<int:pipeline_id>/details/", views.get_pipeline, name='get_pipeline'),
    path("pipelines/<int:pipeline_id>/runs/", views.pipeline_history)
]