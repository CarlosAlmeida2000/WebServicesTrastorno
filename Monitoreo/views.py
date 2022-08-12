from rest_framework.views import APIView
from rest_framework.response import Response
from Monitoreo.reconocimiento import Expresion
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

class Capturando(APIView):
   
    def put(self, request, format = None):
        if request.method == 'PUT':
            try:
                expresion = Expresion()
                json_data = json.loads(request.body.decode('utf-8'))
                if json_data['monitoreando']:
                    expresion.reconocer()
                else:
                    expresion.__del__
                return Response({'capturando': json_data['monitoreando']})
            except Exception as e: 
                return Response({'capturando': 'error'+str(e)})