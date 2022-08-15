from datetime import datetime
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from Monitoreo.models import Vigilancia, Historial
from django.db.models import Q
from Persona.models import Custodiados
from urllib.request import urlopen
from PIL import Image as im
import os
import cv2
import numpy as np

class ExpresionFacial:
    def __init__(self):
        # atributos generales 
        self.dataTrained = 'media\\Perfiles\\Trained'
        self.rutaModelos = 'Monitoreo\\trained_model\\'
        self.custodiadosReconocer = []
        self.expresion_facial = ''
        self.custodiado = Custodiados()
        self.minutosDeteccion = 1
        # Creación de la red neuronal
        self.model = Sequential()
        # neurona
        self.model.add(Conv2D(32, kernel_size = (3, 3), activation = 'relu', input_shape = (48, 48, 1)))
        self.model.add(Conv2D(64, kernel_size = (3, 3), activation = 'relu'))
        self.model.add(MaxPooling2D(pool_size = (2, 2)))
        self.model.add(Dropout(0.25))
        # neurona
        self.model.add(Conv2D(128, kernel_size = (3, 3), activation = 'relu'))
        self.model.add(MaxPooling2D(pool_size = (2, 2)))
        self.model.add(Conv2D(128, kernel_size = (3, 3), activation = 'relu'))
        self.model.add(MaxPooling2D(pool_size = (2, 2)))
        self.model.add(Dropout(0.25))
        # neurona
        self.model.add(Flatten())
        self.model.add(Dense(1024, activation = 'relu'))
        self.model.add(Dropout(0.5))
        self.model.add(Dense(7, activation = 'softmax'))
        # evita el uso de openCL y los mensajes de registro innecesarios
        cv2.ocl.setUseOpenCL(False)
        # diccionario que asigna a cada etiqueta una emoción (orden alfabético)
        self.emotion_dict = {0: 'Enfadado', 1: 'Asqueado', 2: 'Temeroso', 3: 'Feliz', 4: 'Neutral', 5: 'Triste', 6: 'Sorprendido'}
        # cargar el detector de rostros
        self.faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # cargar el modelo entrenado para reconocer expresiones faciales
        self.model.load_weights(self.rutaModelos + 'model.h5')
        # cargar el modelo para el reconocimiento facial
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_recognizer.read(self.rutaModelos + 'modeloLBPHFace.xml')
        # se obtine la lista de personas custodiadas a reconocer
        self.custodiadosReconocer = os.listdir(self.dataTrained)
    
    # se registra el historial de la persona
    def guardarHistorial(self):
        historial = Historial()
        historial.fecha_hora = datetime.now()
        historial.expresion_facial = self.expresion_facial
        historial.custodiado = self.custodiado[0]
        #imagen = im.fromarray(rostro)
        #print("tipo "+ str(type(imagen)))
        #historial.imagen_expresion = imagen
        #historial.imagen_expresion.name = 'persona_id_' + persona_id + '_fecha' + str(historial.fecha_hora)
        historial.save()

    def reconocer(self):
        # iniciar la alimentación de la webcam
        stream = urlopen('http://192.168.0.103:81/stream')
        byte = bytes()
        while (Vigilancia.objects.filter().first().estado):
            byte += stream.read(4096)
            a = byte.find(b'\xff\xd8')
            b = byte.find(b'\xff\xd9')
            if a != -1 and b != -1:
                imagen = byte[a:b + 2]
                byte = byte[b + 2:]
                if imagen :
                    video = cv2.imdecode(np.fromstring(imagen, dtype = np.uint8), cv2.IMREAD_COLOR)
                    # Encuentra la cascada haar para dibujar la caja delimitadora alrededor de la cara
                    gray = cv2.cvtColor(video, cv2.COLOR_BGR2GRAY)
                    auxFrame = gray.copy()
                    # detectando rostros
                    faces = self.faceClassif.detectMultiScale(gray, scaleFactor = 1.3, minNeighbors = 5)
                    # recorriendo rostros 
                    for (x, y, w, h) in faces:
                        rostro = auxFrame[y:y + h, x:x + w]
                        # reconocimiento facial
                        rostro = cv2.resize(rostro, (150, 150), interpolation = cv2.INTER_CUBIC)
                        persona_identif = self.face_recognizer.predict(rostro)
                        cv2.putText(video,'{}'.format(persona_identif),(x, y - 5),1,1.3,(255, 255, 0), 1, cv2.LINE_AA)
                        # se verifica si es la persona
                        if persona_identif[1] < 70:
                            persona_id = self.custodiadosReconocer[persona_identif[0]]
                            self.custodiado = Custodiados.objects.filter(persona_id = persona_id).select_related('persona')
                            if(len(self.custodiado)):
                                cv2.putText(video,'{}'.format(self.custodiado[0].persona.nombres),(x, y - 25), 2, 1.1,(0, 255, 0),1,cv2.LINE_AA)
                                cv2.rectangle(video, (x, y),(x + w,y + h),(0, 255, 0), 2)
                                # se reconoce la expresión facial
                                cv2.rectangle(video, (x, y-50), (x + w, y + h + 10), (255, 0, 0), 2)
                                cropped_img = np.expand_dims(np.expand_dims(cv2.resize(rostro, (48, 48)), -1), 0)
                                prediction = self.model.predict(cropped_img)
                                maxindex = int(np.argmax(prediction))
                                self.expresion_facial = self.emotion_dict[maxindex]
                                cv2.putText(video, self.expresion_facial, (x + 20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                                # se verifica si la última expresión facial registrada en el historial es igual a la expresión facial actual detectada, 
                                # con el objetivo de no registrar un nuevo historial con esa misma fecha y hora
                                ultimo_historial = (Historial.objects.filter(Q(custodiado_id = self.custodiado[0].id) & Q(expresion_facial = self.expresion_facial)).order_by('-fecha_hora'))
                                if(len(ultimo_historial) > 0):
                                    fecha_historial = datetime.strptime(ultimo_historial[0].fecha_hora.strftime('%Y-%m-%d %H:%M:%S.%f') , '%Y-%m-%d %H:%M:%S.%f')
                                    minutos = (datetime.now() - fecha_historial).seconds * 0.0167
                                    if (minutos > self.minutosDeteccion):
                                        self.guardarHistorial()
                                else:
                                    self.guardarHistorial()
                        else:
                            cv2.putText(video,'Desconocido',(x, y - 20), 2, 0.8,(0, 0, 255),1,cv2.LINE_AA)
                            cv2.rectangle(video, (x, y),(x + w, y + h),(0, 0, 255), 2)
                    cv2.imshow('Video', cv2.resize(video,(1600, 860), interpolation = cv2.INTER_CUBIC))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        