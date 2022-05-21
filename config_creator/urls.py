from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('generate/<str:template>', views.generate, name='generate'),
]
