from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:template>', views.genform, name='genform'),
    path('generate/<str:template>', views.generate, name='generate'),
]
