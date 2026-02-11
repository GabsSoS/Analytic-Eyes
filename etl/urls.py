from django.urls import path
from . import views

urlpatterns = [
    path('', views.ETLsListAPIView.as_view(), name='etl-list'),
    path('<int:id>/', views.ETLsListAPIView.as_view(), name='etl-detail'),

]