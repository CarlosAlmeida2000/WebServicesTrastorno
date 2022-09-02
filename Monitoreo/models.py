from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from Persona.models import Custodiados
from Persona.image import Image
from sklearn import linear_model

# Create your models here.

class Vigilancia(models.Model):
    estado = models.BooleanField()

class Historial(models.Model):
    fecha_hora = models.DateTimeField()
    dia = models.IntegerField()
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
            historial = historial.values('id', 'fecha_hora', 'dia', 'expresion_facial', 'custodiado_id', 'custodiado__persona__nombres', 'custodiado__persona__apellidos', 'custodiado__persona__cedula', 'imagen_expresion')
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
                historial = cus.historial_custodiado.all().values()
                if (len(historial)):
                    # calcular los días que se llevan de registro en el historial
                    fecha_minima = (historial.order_by('fecha_hora'))[0]['fecha_hora']
                    fecha_maxima = (historial.order_by('-fecha_hora'))[0]['fecha_hora']
                    # Si existe una semana de registro del historial, se predice el trastorno
                    prediccion = 'Para la predicción del trastorno se debe tener 7 días de registros en el historial'
                    total_dias = historial.order_by('-dia')[0]['dia']
                    if(total_dias > 1):
                        prediccion = Historial.prediccion_trastorno(total_dias, historial)

                    object_json =  { 
                    'fecha_inicio_fin': 'Desde '+ str(fecha_minima.strftime('%Y-%m-%d %H:%M')) + ' hasta ' + str(fecha_maxima.strftime('%Y-%m-%d %H:%M')),
                    'custodiado__persona__nombres': cus.persona.nombres,
                    'custodiado__persona__apellidos': cus.persona.apellidos,
                    'custodiado__persona__cedula': cus.persona.cedula,
                    'dias_historial': total_dias,
                    'enfadado': (historial.filter(expresion_facial = 'Enfadado').count()),
                    'asqueado': (historial.filter(expresion_facial = 'Asqueado').count()),
                    'temeroso': (historial.filter(expresion_facial = 'Temeroso').count()),
                    'feliz': (historial.filter(expresion_facial = 'Feliz').count()),
                    'neutral': (historial.filter(expresion_facial = 'Neutral').count()),
                    'triste': (historial.filter(expresion_facial = 'Triste').count()),
                    'sorprendido': (historial.filter(expresion_facial = 'Sorprendido').count()),
                    'prediccion_trastorno': prediccion
                    }
                    historial_grafico.append(object_json)
            return historial_grafico
        except Custodiados.DoesNotExist:    
            return []
        except Exception as e: 
            return 'error'

    @staticmethod
    def prediccion_trastorno(total_dias, historial):
        frecuencia_enfadado = list()
        frecuencia_asqueado = list()
        frecuencia_temeroso = list()
        frecuencia_feliz = list()
        frecuencia_neutral = list()
        frecuencia_triste = list()
        frecuencia_sorprendido = list()
        dias_historial = list()
        predicciones_emocion = list()

        dias_historial = [[(i + 1)] for i in range(total_dias)]
        print(dias_historial)

        for d in dias_historial:
            frecuencia_enfadado.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Enfadado')).count())
            frecuencia_asqueado.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Asqueado')).count())
            frecuencia_temeroso.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Temeroso')).count())
            frecuencia_feliz.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Feliz')).count())
            frecuencia_neutral.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Neutral')).count())
            frecuencia_triste.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Triste')).count())
            frecuencia_sorprendido.append(historial.filter(Q(dia = d[0]) & Q(expresion_facial = 'Sorprendido')).count())
        
        print('Enfadado: ', frecuencia_enfadado)
        print('Asqueado: ', frecuencia_asqueado)
        print('Temeroso:', frecuencia_temeroso)
        print('Feliz: ', frecuencia_feliz)
        print('Neutral: ', frecuencia_neutral)
        print('Triste:', frecuencia_triste)
        print('Sorprendido: ', frecuencia_sorprendido)
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_enfadado, (total_dias + 1)))
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_asqueado, (total_dias + 1)))
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_temeroso, (total_dias + 1)))
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_feliz, (total_dias + 1)))
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_neutral, (total_dias + 1)))
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_triste, (total_dias + 1)))
        predicciones_emocion.append(Historial.regresion_logistica(dias_historial, frecuencia_sorprendido, (total_dias + 1)))

        print('prediciones de cada emoción: ', predicciones_emocion)




        return ''

    @staticmethod
    def regresion_logistica(x_train, y_train, x_prediction):
        # Creamos el objeto de Regresión Logística
        regresion = linear_model.LogisticRegression()
        # Entrenamos nuestro modelo
        regresion.fit(x_train, y_train) 
        # Predicción de ocurrencua de una emoción dado un día x
        return int(regresion.predict([[x_prediction]]))
        