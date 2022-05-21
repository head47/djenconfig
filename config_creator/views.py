from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def index(request):
    template = loader.get_template('config_creator/index.html')
    context = {}
    response = HttpResponse(template.render(context, request))
    return response
