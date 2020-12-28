# -*- coding: utf-8 -*-

'''
โปรแกรม face recognition ที่รับรายชื่อจาก firebase และมี Switch กดเพื่อ Train ใบหน้า

'''

import cv2
import numpy as np
import os 
from time import sleep           #Library สำหรับเล่นไฟล .mp3
import RPi.GPIO as GPIO
#from firebase import firebase
from PIL import Image

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

#ปุ่มกดเพื่อ Train ใบหน้า เปนแบบ pull_up
sw_train = 12
GPIO.setup(sw_train, GPIO.IN, pull_up_down=GPIO.PUD_UP)

cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video width
cam.set(4, 480) # set video height


# url ของโปรเจค Firebase
#url = "https://raspberry-pi-with-fireba-ee139.firebaseio.com/"
#firebase = firebase.FirebaseApplication(url)

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# เลือกโฟลเดอร์ที่เก็บไฟล์ ตรวจจับและ Cap ใบหน้า จากโปรแกรม 01_face_dataset.py
path = 'dataset'

recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml");

# function to get the images and label data
def getImagesAndLabels(path):

    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
    faceSamples=[]
    ids = []

    for imagePath in imagePaths:

        PIL_img = Image.open(imagePath).convert('L') # convert it to grayscale
        img_numpy = np.array(PIL_img,'uint8')

        id = int(os.path.split(imagePath)[-1].split(".")[1])
        faces = detector.detectMultiScale(img_numpy)

        for (x,y,w,h) in faces:
            faceSamples.append(img_numpy[y:y+h,x:x+w])
            ids.append(id)

    return faceSamples,ids

face_id = 0
count = 0
id_counter = 1
sw_status = 0

while 1:
    print('press sw to train...')
    # For each person, enter one numeric face id
    if GPIO.input(sw_train) == 0:
        face_id = id_counter
        sw_status = 1

    if sw_status == 1:   
        print("\n [INFO] Initializing face capture. Look the camera and wait ...")

        while 1: 
            ret, img = cam.read()
            img = cv2.flip(img, 1) # flip video image vertically
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.3, 5)      

            for (x,y,w,h) in faces:

                cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
                count += 1
                print(count)

                # Save the captured image into the datasets folder
                cv2.imwrite("test_dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])
                cv2.imshow('image', img)

            k = cv2.waitKey(100) & 0xff # Press 'ESC' for exiting video
            if k == 27:
                break
            elif count >= 30: # Take 30 face sample and stop video
                break

        sw_status = 0
        id_counter += 1
        
        cam.release()
        cv2.destroyAllWindows()
################################################################################

        print ("\n [INFO] Training faces. It will take a few seconds. Wait ...")
        faces,ids = getImagesAndLabels(path)
        recognizer.train(faces, np.array(ids))

        # Save โมเดลที่ trainer/trainer.yml
        recognizer.write('test_trainer/trainer.yml') # recognizer.save() worked on Mac, but not on Pi

        # Print the numer of faces trained and end program
        print("\n [INFO] {0} faces trained. Exiting Program".format(len(np.unique(ids))))
        # Do a bit of cleanup
        print("\n [INFO] Exiting Program and cleanup stuff")

    sleep(0.3)