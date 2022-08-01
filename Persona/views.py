from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
import json

# Create your views here.
class Cuidador(APIView):
    def get(self, request, format = None):
        if request.method == 'GET':
            try:
                return Response({'usuario': Usuarios.obtener_datos(request)})
            except Exception as e:
                return Response({'usuario': 'error'})
        
    def post(self, request, format = None):
        if request.method == 'POST':
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                usuario = Usuarios()
                return Response({'usuario': usuario.guardar(json_data)})
            except Exception as e: 
                return Response({'usuario': 'error'})
    
    def put(self, request, format = None):
        if request.method == 'PUT':
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                usuario = Usuarios.objects.get(id = json_data['id'])
                return Response({'usuario': usuario.guardar(json_data)})
            except Exception as e: 
                return Response({'usuario': 'error'})

class Autenticacion(APIView):
    def post(self, request, format = None):
        if request.method == 'POST':
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                return Response({'usuario': Usuarios.login(json_data)})
            except Exception as e: 
                return Response({'usuario': 'error'})

class Custodiado(APIView):
    def get(self, request, format = None):
        if request.method == 'GET':
            try:
                return Response({'custodiado': Custodiados.obtener_datos(request)})
            except Exception as e:
                return Response({'custodiado': 'error'})

    def post(self, request, format = None):
        if request.method == 'POST':
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                custodiado = Custodiados()
                return Response({'custodiado': custodiado.guardar(json_data)})
            except Exception as e: 
                return Response({'custodiado': 'error'})

    def put(self, request, format = None):
        if request.method == 'PUT':
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                custodiado = Custodiados.objects.get(id = json_data['id'])
                return Response({'custodiado': custodiado.guardar(json_data)})
            except Exception as e: 
                return Response({'custodiado': 'error'})