from datetime import datetime
import numpy as np
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from Monitoreo.models import Historial
from Persona.models import Custodiados
from urllib.request import urlopen
from PIL import Image as im
import os

class Expresion:
    def __init__(self):
        self.dataTrained = 'media\\Perfiles\\Trained'
        self.rutaModelos = 'Monitoreo\\trained_model\\'
        self.custodiadosReconocer = []
        self.expresion_facial = ''
        self.chao = True
    
    def __del__(self):
        self.chao = False
        print("chaoo")

    def estado(self):
        return self.chao

    def reconocer(self):
        # Create the model
        model = Sequential()
        # neurona
        model.add(Conv2D(32, kernel_size = (3, 3), activation = 'relu', input_shape = (48, 48, 1)))
        model.add(Conv2D(64, kernel_size = (3, 3), activation = 'relu'))
        model.add(MaxPooling2D(pool_size = (2, 2)))
        model.add(Dropout(0.25))
        # neurona
        model.add(Conv2D(128, kernel_size = (3, 3), activation = 'relu'))
        model.add(MaxPooling2D(pool_size = (2, 2)))
        model.add(Conv2D(128, kernel_size = (3, 3), activation = 'relu'))
        model.add(MaxPooling2D(pool_size = (2, 2)))
        model.add(Dropout(0.25))
        # neurona
        model.add(Flatten())
        model.add(Dense(1024, activation = 'relu'))
        model.add(Dropout(0.5))
        model.add(Dense(7, activation = 'softmax'))
        # evita el uso de openCL y los mensajes de registro innecesarios
        cv2.ocl.setUseOpenCL(False)
        # diccionario que asigna a cada etiqueta una emoción (orden alfabético)
        emotion_dict = {0: "Enfadado", 1: "Asqueado", 2: "Temeroso", 3: "Feliz", 4: "Neutral", 5: "Triste", 6: "Sorprendido"}
        # cargar el detector de rostros
        faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # cargar el modelo entrenado para reconocer expresiones faciales
        model.load_weights(self.rutaModelos + 'model.h5')
        # cargar el modelo para el reconocimiento facial
        face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        face_recognizer.read(self.rutaModelos + 'modeloLBPHFace.xml')
        # se obtine la lista de personas custodiadas a reconocer
        self.custodiadosReconocer = os.listdir(self.dataTrained)
        # iniciar la alimentación de la webcam
        stream = urlopen('http://192.168.0.103:81/stream')
        byte = bytes()
        while self.estado():
            print("sii")
            byte += stream.read(4096)
            a = byte.find(b'\xff\xd8')
            b = byte.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = byte[a:b + 2]
                byte = byte[b + 2:]
                if jpg :
                    video = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    # Encuentra la cascada haar para dibujar la caja delimitadora alrededor de la cara
                    gray = cv2.cvtColor(video, cv2.COLOR_BGR2GRAY)
                    auxFrame = gray.copy()
                    # detectando rostros
                    faces = faceClassif.detectMultiScale(gray, scaleFactor = 1.3, minNeighbors = 5)
                    # recorriendo rostros 
                    for (x, y, w, h) in faces:
                        rostro = auxFrame[y:y + h, x:x + w]
                        # reconocimiento facial
                        rostro = cv2.resize(rostro, (150, 150), interpolation = cv2.INTER_CUBIC)
                        persona_identif = face_recognizer.predict(rostro)
                        cv2.putText(video,'{}'.format(persona_identif),(x, y - 5),1,1.3,(255, 255, 0), 1, cv2.LINE_AA)
                        # se verifica si es la persona
                        if persona_identif[1] < 70:
                            persona_id = self.custodiadosReconocer[persona_identif[0]]



                            custodiado = (Custodiados.objects.get(persona_id = persona_id))



                            cv2.putText(video,'{}'.format(custodiado.persona.nombres),(x, y - 25), 2, 1.1,(0, 255, 0),1,cv2.LINE_AA)
                            cv2.rectangle(video, (x, y),(x + w,y + h),(0, 255, 0), 2)
                            # se reconoce la expresión facial
                            cv2.rectangle(video, (x, y-50), (x + w, y + h + 10), (255, 0, 0), 2)
                            cropped_img = np.expand_dims(np.expand_dims(cv2.resize(rostro, (48, 48)), -1), 0)
                            prediction = model.predict(cropped_img)
                            maxindex = int(np.argmax(prediction))
                            self.expresion_facial = emotion_dict[maxindex]
                            cv2.putText(video, self.expresion_facial, (x + 20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                            # se registra el historial de la persona con su expresión facial
                            historial = Historial()
                            historial.fecha_hora = datetime.now()
                            historial.expresion_facial = self.expresion_facial
                            historial.custodiado = custodiado
                            #imagen = im.fromarray(rostro)
                            #print("tipo "+ str(type(imagen)))
                            #historial.imagen_expresion = imagen
                            #historial.imagen_expresion.name = 'persona_id_' + persona_id + '_fecha' + str(historial.fecha_hora)
                            historial.save()
                        else:
                            cv2.putText(video,'Desconocido',(x, y - 20), 2, 0.8,(0, 0, 255),1,cv2.LINE_AA)
                            cv2.rectangle(video, (x, y),(x + w, y + h),(0, 0, 255), 2)
                    cv2.imshow('Video', cv2.resize(video,(1600, 960), interpolation = cv2.INTER_CUBIC))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        video = None
        cv2.destroyAllWindows()
        