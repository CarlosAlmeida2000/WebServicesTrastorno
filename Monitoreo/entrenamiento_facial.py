import os
import cv2
import imutils
import numpy as np
class EntrenamientoFacial:
    def __init__(self):
        self.dataPath = 'media\\Perfiles'
        self.dataTrained = 'media\\Perfiles\\Trained'
        self.rutaModelos = 'Monitoreo\\trained_model\\'
        self.labels = []
        self.facesData = []
        self.label = 0
        self.faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def entrenar(self):
        try:
            os.makedirs(self.dataTrained, exist_ok=True)
            # preparacion de imágenes a entrenar
            peopleList = os.listdir(self.dataPath)
            # se elimina la carpeta "Trained", SOLO quedan las carpetas de los perfiles
            peopleList.pop(len(peopleList) -1)
            for nameDir in peopleList:
                personPath = self.dataPath + '\\' + str(nameDir)
                count = 0
                for fileName in os.listdir(personPath):
                    #print(personPath + '\\' + str(fileName))
                    if personPath != '' and str(fileName) != '':
                        img = cv2.imread(personPath + '\\' + str(fileName))
                        frame =  imutils.resize(img, width = 640)
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        auxFrame = frame.copy()
                        faces = self.faceClassif.detectMultiScale(gray, 1.3, 5)
                        for (x,y,w,h) in faces:
                            cv2.rectangle(frame, (x, y),(x + w, y + h),(0, 255, 0), 2)
                            rostro = auxFrame[y:y + h, x:x + w]
                            rostro = cv2.resize(rostro,(150, 150),interpolation = cv2.INTER_CUBIC)
                            os.makedirs(self.dataTrained + '\\' + str(nameDir), exist_ok=True)
                            cv2.imwrite(self.dataTrained + '\\' + str(nameDir) + '\\rotro_{}.png'.format(count), rostro)
                    count = count + 1
            # entrenamiento del modelo
            peopleList = os.listdir(self.dataTrained)
            for nameDir in peopleList:
                personPath = self.dataTrained + '\\' + nameDir
                #print('Leyendo las imágenes')
                for fileName in os.listdir(personPath):
                    #print('Rostros: ', nameDir + '\\' + str(fileName))
                    self.labels.append(self.label)
                    self.facesData.append(cv2.imread(personPath+'\\' + str(fileName), 0))
                self.label = self.label + 1
            face_recognizer = cv2.face.LBPHFaceRecognizer_create()
            #print("Entrenando...")
            face_recognizer.train(self.facesData, np.array(self.labels)) 
            face_recognizer.write(self.rutaModelos + 'modeloLBPHFace.xml')
            print("Modelo almacenado...")
        except Exception as e: 
            return None
