from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from Persona.models import Custodiados
from Persona.image import Image
from datetime import date

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
            historial = historial.values('id', 'fecha_hora', 'expresion_facial', 'custodiado_id', 'custodiado__persona__nombres', 'custodiado__persona__apellidos', 'custodiado__persona__cedula', 'imagen_expresion')
            file = Image()
            for u in range(len(historial)):
                if(historial[u]['imagen_expresion'] != ''):
                    file.ruta = historial[u]['imagen_expresion']
                    historial[u]['imagen_expresion'] = file.get_base64()
            return list(historial)
        except Exception as e: 
            return 'error'
    
    @staticmethod
    def crearJson(custodiados, historial, grafico_general):
        fecha_minima = (historial.order_by('fecha_hora'))[0]['fecha_hora']
        fecha_maxima = (historial.order_by('-fecha_hora'))[0]['fecha_hora']
        # calcular los días que se llevan de registro en el historial
        fecha_actual = date(int(str(fecha_minima.strftime('%Y'))), 
                            int(str(fecha_minima.strftime('%m'))), 
                            int(str(fecha_minima.strftime('%d'))))
        fecha_fin = date(int(str(fecha_maxima.strftime('%Y'))), 
                        int(str(fecha_maxima.strftime('%m'))), 
                        int(str(fecha_maxima.strftime('%d'))))
        diferencia = fecha_fin - fecha_actual
        
        if grafico_general:
            historial_grafico =  [{ 
            'fecha_inicio_fin': 'Desde '+ str(fecha_minima.strftime('%Y-%m-%d %H:%M')) + ' hasta ' + str(fecha_maxima.strftime('%Y-%m-%d %H:%M')),
            'dias_historial': diferencia.days,
            'enfadado': (historial.filter(expresion_facial = 'Enfadado').count()),
            'asqueado': (historial.filter(expresion_facial = 'Asqueado').count()),
            'temeroso': (historial.filter(expresion_facial = 'Temeroso').count()),
            'feliz': (historial.filter(expresion_facial = 'Feliz').count()),
            'neutral': (historial.filter(expresion_facial = 'Neutral').count()),
            'triste': (historial.filter(expresion_facial = 'Triste').count()),
            'sorprendido': (historial.filter(expresion_facial = 'Sorprendido').count()),
            }]
        else:
            historial_grafico =  [{ 
            'fecha_inicio_fin': 'Desde '+ str(fecha_minima.strftime('%Y-%m-%d %H:%M')) + ' hasta ' + str(fecha_maxima.strftime('%Y-%m-%d %H:%M')),
            'custodiado__persona__nombres': custodiados.persona.nombres,
            'custodiado__persona__apellidos': custodiados.persona.apellidos,
            'custodiado__persona__cedula': custodiados.persona.cedula,
            'dias_historial': diferencia.days,
            'enfadado': (historial.filter(expresion_facial = 'Enfadado').count()),
            'asqueado': (historial.filter(expresion_facial = 'Asqueado').count()),
            'temeroso': (historial.filter(expresion_facial = 'Temeroso').count()),
            'feliz': (historial.filter(expresion_facial = 'Feliz').count()),
            'neutral': (historial.filter(expresion_facial = 'Neutral').count()),
            'triste': (historial.filter(expresion_facial = 'Triste').count()),
            'sorprendido': (historial.filter(expresion_facial = 'Sorprendido').count()),
            'prediccion_trastorno': str(0.00)
            }]
        return historial_grafico

    @staticmethod
    def obtener_grafico(request):
        try:
            custodiados = Custodiados()
            grafico_general = False
            if 'persona__cedula' in request.GET and 'cuidador_id' in request.GET:
                custodiados = Custodiados.objects.filter(Q(persona__cedula__icontains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['cuidador_id'])).first()   
            elif 'nombres_apellidos' in request.GET and 'cuidador_id' in request.GET:
                custodiados = (Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id'])).annotate(nombres_completos = Concat('persona__nombres', Value(' '), 'persona__apellidos'))
                custodiados = custodiados.filter(nombres_completos__icontains = request.GET['nombres_apellidos']).first()
            elif 'cuidador_id' in request.GET:
                grafico_general = True
                custodiados = Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id'])
            if grafico_general:
                historial = Historial.objects.all().exclude(~Q(custodiado_id__in = custodiados.values('id'))).values()
                return Historial.crearJson(custodiados, historial, grafico_general)
            else:
                historial = custodiados.historial_custodiado.all().values()
                return Historial.crearJson(custodiados, historial, grafico_general)
        except Custodiados.DoesNotExist:    
            return []
        except Exception as e: 
            return 'error'