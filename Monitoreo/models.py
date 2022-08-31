from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from Persona.models import Custodiados
from Persona.image import Image
from datetime import date, datetime

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
    def obtener_grafico(request):
        try:
            custodiados = Custodiados()
            if 'persona__cedula' in request.GET and 'cuidador_id' in request.GET:
                custodiados = Custodiados.objects.filter(Q(persona__cedula__icontains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['cuidador_id']))
            elif 'nombres_apellidos' in request.GET and 'cuidador_id' in request.GET:
                custodiados = (Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id'])).annotate(nombres_completos = Concat('persona__nombres', Value(' '), 'persona__apellidos'))
                custodiados = custodiados.filter(nombres_completos__icontains = request.GET['nombres_apellidos'])
            elif 'cuidador_id' in request.GET:
                custodiados = Custodiados.objects.filter(cuidador__pk = request.GET['cuidador_id'])
            historial_grafico = []
            for cus in custodiados: 
                historial = cus.historial_custodiado.all()
                enfadado = 0
                asqueado = 0
                temeroso = 0
                feliz = 0
                neutral = 0
                triste = 0
                sorprendido = 0
                nombres = ''
                apellidos = ''
                cedula = ''
                una = True
                for his in historial:
                    if una:
                        fecha_minima = his.fecha_hora
                        fecha_maxima = his.fecha_hora
                        una = False
                    f_minima = his.fecha_hora
                    f_maxima = his.fecha_hora
                    nombres = his.custodiado.persona.nombres
                    apellidos = his.custodiado.persona.apellidos
                    cedula = his.custodiado.persona.cedula
                    if his.expresion_facial == 'Enfadado':
                        enfadado += 1
                    if his.expresion_facial == 'Asqueado':
                        asqueado += 1
                    if his.expresion_facial == 'Temeroso':
                        temeroso += 1
                    if his.expresion_facial == 'Feliz':
                        feliz += 1
                    if his.expresion_facial == 'Neutral':
                        neutral += 1
                    if his.expresion_facial == 'Triste':
                        triste += 1
                    if his.expresion_facial == 'Sorprendido':
                        sorprendido += 1
                    if f_minima < fecha_minima:
                        fecha_minima = his.fecha_hora
                    if f_maxima > fecha_maxima:
                        fecha_maxima = his.fecha_hora

                # calcular los días que se llevan de registro en el historial
                fecha_actual = date(int(str(fecha_minima.strftime('%Y'))), 
                                    int(str(fecha_minima.strftime('%m'))), 
                                    int(str(fecha_minima.strftime('%d'))))
                fecha_fin = date(int(str(fecha_maxima.strftime('%Y'))), 
                                int(str(fecha_maxima.strftime('%m'))), 
                                int(str(fecha_maxima.strftime('%d'))))
                diferencia = fecha_fin - fecha_actual
                object_json =  { 
                'fecha_inicio_fin': 'Desde '+ str(fecha_minima.strftime('%Y-%m-%d %H:%M')) + ' hasta ' + str(fecha_maxima.strftime('%Y-%m-%d %H:%M')),
                'custodiado__persona__nombres': nombres,
                'custodiado__persona__apellidos': apellidos,
                'custodiado__persona__cedula': cedula,
                'dias_historial': diferencia.days,
                'enfadado': enfadado,
                'asqueado': asqueado,
                'temeroso': temeroso,
                'feliz': feliz,
                'neutral': neutral,
                'triste': triste,
                'sorprendido': sorprendido,
                'prediccion_trastorno': str(0.00)
                }
                historial_grafico.append(object_json)
            return historial_grafico
        except Custodiados.DoesNotExist:    
            return []
        except Exception as e: 
            return 'error'