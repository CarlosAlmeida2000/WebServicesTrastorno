from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from Persona.models import Custodiados
from Persona.image import Image
from datetime import datetime

# Create your models here.

class Vigilancia(models.Model):
    estado = models.BooleanField()

class Historial(models.Model):
    fecha_hora = models.DateTimeField()
    imagen_expresion = models.ImageField(upload_to = 'Expresiones_detectadas', null = True, blank = True)
    expresion_facial = models.CharField(max_length = 15)
    custodiado = models.ForeignKey('Persona.Custodiados', on_delete = models.PROTECT, related_name = "historial_custodiado")

    @staticmethod
    def obtener_historial(request):
        try:
            if 'persona__cedula' in request.GET and 'cuidador_id' in request.GET:
                custodiados = Custodiados.objects.filter(Q(persona__cedula__icontains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['cuidador_id']))   
                historial = Historial.objects.all().exclude(~Q(custodiado_id__in = custodiados.values('id')))
            elif 'nombres_apellidos' in request.GET and 'cuidador_id' in request.GET:
                custodiados = (Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id']).select_related('persona')).annotate(nombres_completos = Concat('persona__nombres', Value(' '), 'persona__apellidos'))
                custodiados = custodiados.filter(nombres_completos__icontains = request.GET['nombres_apellidos'])
                historial = Historial.objects.all().exclude(~Q(custodiado_id__in = custodiados.values('id')))
            elif 'cuidador_id' in request.GET:
                custodiados = Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id'])
                historial = Historial.objects.all().exclude(~Q(custodiado_id__in = custodiados.values('id')))
            else:
                custodiados = Custodiados.objects.all()
                historial = Historial.objects.all().exclude(~Q(custodiado_id__in = custodiados.values('id')))
            historial = historial.values('id', 'fecha_hora', 'expresion_facial', 'custodiado_id', 'custodiado__persona__nombres', 'imagen_expresion')
            file = Image()
            for u in range(len(historial)):
                if(historial[u]['imagen_expresion'] != ''):
                    file.ruta = historial[u]['imagen_expresion']
                    historial[u]['imagen_expresion'] = file.get_base64()
            return list(historial)
        except Exception as e: 
            return 'error'
        
    @staticmethod
    def obtener_grafico(request):
        try:
            if 'persona__cedula' in request.GET and 'cuidador_id' in request.GET:
                custodiado = Custodiados.objects.get(Q(persona__cedula__icontains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['cuidador_id']))   
            elif 'nombres_apellidos' in request.GET and 'cuidador_id' in request.GET:
                custodiado = (Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id']).select_related('persona')).annotate(nombres_completos = Concat('persona__nombres', Value(' '), 'persona__apellidos'))
                custodiado = custodiado.get(nombres_completos__icontains = request.GET['nombres_apellidos'])
            if custodiado:
                historial = custodiado.historial_custodiado.all().values()
                fecha_minima = (historial.order_by('fecha_hora'))[0]['fecha_hora']
                fecha_maxima = (historial.order_by('-fecha_hora'))[0]['fecha_hora']
                historial_grafico =  [{
                    'custodiado__persona__nombres': custodiado.persona.nombres,
                    'fecha_inicio_fin': 'Desde '+ str(fecha_minima.strftime('%Y-%m-%d %H:%M')) + ' hasta ' + str(fecha_maxima.strftime('%Y-%m-%d %H:%M')),
                    'enfadado': (historial.filter(expresion_facial = 'Enfadado').count()),
                    'asqueado': (historial.filter(expresion_facial = 'Asqueado').count()),
                    'temeroso': (historial.filter(expresion_facial = 'Temeroso').count()),
                    'feliz': (historial.filter(expresion_facial = 'Feliz').count()),
                    'neutral': (historial.filter(expresion_facial = 'Neutral').count()),
                    'triste': (historial.filter(expresion_facial = 'Triste').count()),
                    'sorprendido': (historial.filter(expresion_facial = 'Sorprendido').count()),
                    # AQUI EJECUTAR EL ALGORITMO DE PREDICCIÓN
                    'prediccion_trastorno': 0.0
                }]
                return historial_grafico
            else:
                return []
        except Custodiados.DoesNotExist:    
            return []
        except Exception as e: 
            return 'error'