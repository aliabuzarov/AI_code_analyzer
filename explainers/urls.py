"""
URL configuration for explainers app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/explain/', views.explain_api, name='explain_api'),
]

