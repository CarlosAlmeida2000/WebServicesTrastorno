from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
import json

# Create your views here.
class HistorialCustodiado(APIView):
    def get(self, request, format = None):
        if request.method == 'GET':
            try:
                return Response({'historial': Historial.obtener_historial(request)})
            except Exception as e:
                return Response({'historial': 'error'})

class GraficoCustodiado(APIView):
    def get(self, request, format = None):
        if request.method == 'GET':
            try:
                return Response({'grafico': Historial.obtener_grafico(request)})
            except Exception as e:
                return Response({'grafico': 'error'})

class Monitoreo(APIView):
    def get(self, request, format = None):
        pass
    def post(self, request, format = None):
        pass