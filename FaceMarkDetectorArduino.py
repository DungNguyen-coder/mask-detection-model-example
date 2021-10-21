import os
import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2 as cv
import cv2
from tensorflow._api import v2
import video
import datetime, time
from PIL import Image, ImageOps
import random
import string
import serial
import time
from gtts import gTTS
from pygame import mixer
from datetime import datetime
from tensorflow.keras import *
# import keras
# from keras import*
# import keras.api
# from tensorflow import keras.api.v2


# try :
#     ser = serial.Serial("COM5", 9600)
#     time.sleep(1)
#     print("Cổng COM đã được mở")
# except : pass

com_name = str(input("Nhập tên cổng COM kết nối arduino : "))
ser = serial.Serial(com_name, 9600)
time.sleep(1)
print("Cổng COM đã được mở")

cam_index = int(input("Nhập CAMERA bạn muốn sử dụng : "))

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
print(CURRENT_DIR)

class FaceMask:

    LABELS = []
    cascade = None
    model = None
    size = (224, 224)

    
    def __init__(self):
        # self.cascade = cv2.CascadeClassifier(os.path.join(CURRENT_DIR, "cascade.xml"))

        self.cascade = cv2.CascadeClassifier("cascade.xml")
        if(self.cascade.empty()):
            print("cascade empty")

        self.getLabels()

        modelFile = os.path.join("keras_model.h5")
        if(os.path.exists(modelFile)):
            self.model = tf.keras.models.load_model(modelFile)
        
        #data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
        
        np.set_printoptions(suppress=True)

    ####################################################################################################
    
    def getLabels(self):
        with open(os.path.join("labels_facemask.txt"), 'r') as file:
            for x in file:
                self.LABELS.append(str(x).replace("\n", ""))
        print(self.LABELS)

    ####################################################################################################


# 
    def TFpredictImgPath(self, imgePath):
        pilImg = Image.load_img(imgePath)    

        return self.TFpredictPilImg(pilImg)

    ####################################################################################################

    def TFpredictPilImg(self, pilImg):
        if(self.model == None):
            print("model is null")
            return None
        
        data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)


        #resize the image to a 224x224 with the same strategy as in TM2:
        #resizing the image to be at least 224x224 and then cropping from the center
        image = ImageOps.fit(pilImg, self.size, Image.ANTIALIAS)

        #turn the image into a numpy array
        image_array = np.asarray(image)

        # Normalize the image
        normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

        # Load the image into the array
        data[0] = normalized_image_array

        # run the inference
        predictions = self.model.predict(data)
        result = np.argmax(predictions)
        return result

    ####################################################################################################

    def PredictMat(self, mat):
        img = cv.cvtColor(mat, cv.COLOR_BGR2RGB)    
        img = cv.resize(img, self.size)
        img_pil = Image.fromarray(img)

        result = self.TFpredictPilImg(img_pil)
        return result

    ####################################################################################################

    def DetectFaceInFrame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray = cv2.equalizeHist(gray)

        newWidth = int(gray.shape[1] /2)
        newHeight = int(gray.shape[0] /2)

        gray = cv2.resize(gray, (newWidth, newHeight))
        rects = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, flags=cv2.CASCADE_SCALE_IMAGE, minSize=(20,20))

        if(len(rects) > 0):
            rects[:,2:] += rects[:,:2]

        for r in rects:
            r[0] *= 2
            r[1] *= 2
            r[2] *= 2
            r[3] *= 2
            

        return rects

    ####################################################################################################

    def CropMat(self, frame, rect):
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y

        frame = frame[y:h, x:w]
        return frame

    ####################################################################################################

    def GenerateRandomString(self):
        return ''.join(random.choices(string.ascii_lowercase + "_" + string.ascii_uppercase +  string.digits, k=10))

    ####################################################################################################

    def DetectMask(self, frame):
        startTime = time.time()
        saveImage = False #to debug

        rects = self.DetectFaceInFrame(frame)
        arr = []
        # if(mixer.music.get_busy()) : return frame, arr
        if(len(rects) >= 2) :

            self.speak("Có quá nhiều người trong khung hình, đề nghị mọi người đứng cách nhau để bảo đảm an toàn phòng dịch")
            if(saveImage):
                cv2.imwrite("outface\\" + datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + "_" + self.GenerateRandomString() + ".jpg", frame)
        elif(len(rects) > 0):
            rects[:,2:] += rects[:,:2]
            for rect in rects:
                #print(rect)
                matFace = self.CropMat(frame, rect)                
                predicted = self.PredictMat(matFace)
                result = self.LABELS[predicted]

                color = (0, 0, 255)
                
                
                x1 = rect[0]
                y1 = rect[1]
                x2 = rect[2] - x1
                y2 = rect[3] - y1

                elapsed = time.time() - startTime

                if(saveImage):
                    cv2.imwrite(result +"\\" + datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + "_"  + self.GenerateRandomString() + ".jpg", matFace)

                arr.append(result)

        # mark is detected
                if(result == "Mask"):
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    self.speak("", True)

                    
                elif(result == "Hand" or result == "No mask" or result == "Wrong"):
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    self.speak("Bạn chưa đeo khẩu trang, nếu bạn chưa có khẩu trang xin hãy sử dụng khẩu trang trong hộp")

                if(result != "Nothing"):
                    cv.putText(frame, str(result), (10,60), cv.FONT_HERSHEY_PLAIN, 3, color, thickness = 2)
                    cv.putText(frame, "{:10.2f} s".format(elapsed), (300,60), cv.FONT_HERSHEY_PLAIN, 3, color, thickness = 2)
        else:
            if(saveImage):
                cv2.imwrite("noface\\" + datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + "_" + self.GenerateRandomString() + ".jpg", frame)

        return frame, arr



    def speak(self, text, mask = False):
        try:
            if mixer.music.get_busy() : 
                return
        except : pass

        now = datetime.now()
        nameSound = now.strftime("./sounds/%d%H%M%S.mp3")

        if(mask) :
            # ser.write('1'.encode())
            # s = str(ser.readline())
            # s = s.split("'")[1].split("\\")[0]
            s = "3750"
            tem_object = int(s)/100
            if(tem_object > 38) : text = "Nhiệt độ cơ thể của bạn là " + str(tem_object) + " độ C, nhiệt độ của bạn ở mức cao hãy đến cơ sở y tế để được trợ giúp, chú ý hãy sát khuẩn tay bằng dung dịch sát khuẩn"
            else : text = "Nhiệt độ cơ thể của bạn là " + str(tem_object) + " độ C, cửa đã được mở, chú ý hãy sát khuẩn tay bằng dung dịch sát khuẩn"

        try :
            if text == None : return
            print("Trợ lý P&P: {}".format(text))

            tts = gTTS(text= text, lang= 'vi', slow=False)   # có tác dụng chuyển text sang giọng nói
            
            tts.save(nameSound)
        except : pass
        # playsound.playsound(nameSound, True)   # có tác dụng chạy đoạn giọng nói của trợ lý ảo
        
        try :
            mixer.quit()
        except : pass

        # giúp phát file âm thanh đã lưu
        mixer.init()
        # Loading the song
        mixer.music.load(nameSound)
        # Setting the volume
        mixer.music.set_volume(0.7)

        # Start playing the song
        mixer.music.play()
        

####################################################################################################


faceMask = FaceMask()

if __name__ == '__main__':
    # cap = video.create_capture(0)
    # cap = video.create_capture(1)
    try :
        cap = video.create_capture(cam_index)
    except : 
        print("Lỗi không mở được CAM, mở CAM mặc định thay thế !")
        cap = video.create_capture(0)
        
    while True:
        
        _ret, frame = cap.read()
        frame, arr = faceMask.DetectMask(frame)

        cv.imshow('frame', frame)
        ch = cv.waitKey(20)
        if ch == 27:
            break