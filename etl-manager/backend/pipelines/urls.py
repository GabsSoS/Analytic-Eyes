from django.urls import path
from . import views

urlpatterns = [

    # Rota de login
    path("auth/login/", views.user_login, name='login'),
    
    # Rota para obter informações do usuário autenticado
    path("auth/me/", views.user_info, name='user_info'),
    
    # Rota de alteração de senha
    path("auth/change-password/", views.change_password, name='change_password'),

    # Criação de usuário (ambos os endpoints para compatibilidade)
    path("users/create/", views.create_user, name='create_user'),
    path("auth/create-user/", views.create_user, name='create_user_alt'),

    # Criação de pipeline
    path("pipelines/create/", views.pipeline_create, name='create_pipeline'),
        
    #Execução de pipe e detalhes de uma pipe específica
    path("pipelines/<int:pipeline_id>/", views.trigger_pipeline, name='execute_pipeline'),
    path("pipelines/<int:pipeline_id>/details/", views.get_pipeline, name='get_pipeline'),
    path("pipelines/<int:pipeline_id>/update/", views.update_pipeline, name='update_pipeline'),
    path("pipelines/<int:pipeline_id>/delete/", views.pipeline_delete, name='delete_pipeline'),
    path("pipelines/<int:pipeline_id>/env/", views.manage_pipeline_env, name='manage_pipeline_env'),
   
    # Listagem de pipes
    path("pipelines/", views.pipelines, name='list_pipelines'),
    path("pipelines/stats/", views.pipelines_stats, name='pipelines_stats'),
    
    # Histórico de execuções de uma pipe específica
    path("pipelines/<int:pipeline_id>/runs/", views.pipeline_history),

    # Listagem de usuários
    path("users/", views.list_users, name='list_users')
]
