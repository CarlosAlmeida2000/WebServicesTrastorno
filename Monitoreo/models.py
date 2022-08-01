from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from Persona.models import Custodiados
from Persona.file import File
from datetime import datetime

# Create your models here.
class Historial(models.Model):
    fecha_hora = models.DateField()
    imagen_expresion = models.ImageField(upload_to = 'Expresiones_detectadas', null = True, blank = True)
    expresion_facial = models.CharField(max_length = 15)
    custodiado = models.ForeignKey('Persona.Custodiados', on_delete = models.PROTECT, related_name = "historial_custodiado")

    @staticmethod
    def obtener_historial(request):
        try:
            if 'persona__cedula' in request.GET:
                custodiados = Custodiados.objects.filter(Q(custodiado__cedula__contains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['usuario_id']))   
                historial = Historial.objects.all().exclude(~Q(custodio_id__in = custodiados.values('id')))
            elif 'nombres_apellidos' in request.GET:
                custodiados = (Custodiados.objects.filter(cuidador__pk = request.GET['usuario_id']).select_related('custodiado')).annotate(nombres_completos = Concat('custodiado__nombres', Value(' '), 'custodiado__apellidos'))
                custodiados = custodiados.filter(nombres_completos__contains = request.GET['nombres_apellidos'])
                historial = Historial.objects.all().exclude(~Q(custodio_id__in = custodiados.values('id')))
            else:
                custodiados = Custodiados.objects.filter(cuidador__pk = request.GET['usuario_id'])
                historial = Historial.objects.all().exclude(~Q(custodio_id__in = custodiados.values('id')))


            # file = File()
            # for u in range(len(custodiados)):
            #     if(custodiados[u]['custodiado__foto_perfil'] != ''):
            #         file.ruta = custodiados[u]['custodiado__foto_perfil']
            #         custodiados[u]['custodiado__foto_perfil'] = file.get_base64()

            return list(historial)
        except Exception as e: 
            return 'error'
        
    @staticmethod
    def obtener_grafico(request):
        try:
            if 'persona__cedula' in request.GET:
                custodiado = Custodiados.objects.get(Q(custodiado__cedula__contains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['usuario_id']))   

            elif 'nombres_apellidos' in request.GET:
                custodiado = (Custodiados.objects.filter(cuidador__pk = request.GET['usuario_id']).select_related('custodiado')).annotate(nombres_completos = Concat('custodiado__nombres', Value(' '), 'custodiado__apellidos'))
                custodiado = custodiado.get(nombres_completos__contains = request.GET['nombres_apellidos'])
                
            historial = custodiado.historial_custodiado.all()

            return list(historial)
        except Exception as e: 
            return 'error'