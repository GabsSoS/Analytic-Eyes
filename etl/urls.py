from django.urls import path
from . import views

urlpatterns = [

    #=========== listagens de ETLs  ===========#
    path('', views.ETLsListAPIView.as_view(), name='etl-list'),
    path('<int:id>/', views.ETLsListAPIView.as_view(), name='etl-detail'),
    #==========================================#

    #=========== Alteração de ETLs  ===========#
    path('detail-etl/<int:pk>/', views.ETLRetriveDetailAPIView.as_view(), name="detail-etl")
    #==========================================#
]