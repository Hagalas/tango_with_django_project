from django.shortcuts import render

def handler404(request):
    render (request, '404.html')