from django.urls import path
from . import views

urlpatterns = [

    # Rota de login
    path("auth/login/", views.user_login, name='login'),

    #Criação de usuário
    path("users/create/", views.create_user, name='create_user'),

    # Criação de pipeline
    path("pipelines/create/", views.pipeline_create, name='create_pipeline'),
        
    #Execução de pipe e detalhes de uma pipe específica
    path("pipelines/<int:pipeline_id>/", views.trigger_pipeline, name='execute_pipeline'),
    path("pipelines/<int:pipeline_id>/details/", views.get_pipeline, name='get_pipeline'),
   
    # Listagem de pipes
    path("pipelines/", views.pipelines, name='list_pipelines'),
    
    # Histórico de execuções de uma pipe específica
    path("pipelines/<int:pipeline_id>/runs/", views.pipeline_history)
]