# -*- coding: utf-8 -*-

import cv2
import numpy as np
import os 
import pyttsx3
import multiprocessing as mp
import speech_recognition as sr
from time import sleep
from gtts import gTTS
import pygame           #Library สำหรับเล่นไฟล .mp3
import RPi.GPIO as GPIO
from firebase import firebase
from PIL import Image
import time

pygame.mixer.init()

#ตั้งค่าการเลือกใช้ไมโครโฟน ดูลำดับ 0, 1 ได้โดยการรัน Scan_Divice.py 
r = sr.Recognizer()
speech = sr.Microphone(device_index = 1)         

recognizer = cv2.face.LBPHFaceRecognizer_create()
#เลือกไฟล์ที่ทำการ train เข้ามาเพื่อใช้ตรวจสอบใบหน้า 
recognizer.read('trainer/trainer.yml')
#ไฟล์ที่ใช้สำหรับตรวจจับใบหน้า
cascadePath = 'haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(cascadePath);

#face_detector = cv2.CascadeClassifier(cascadePath)
detector = cv2.CascadeClassifier(cascadePath);

font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize and start realtime video capture Camera1
cam = cv2.VideoCapture(0)
cam.set(4, 1280) # set video widht
cam.set(3, 720) # set video height
# Define min window size to be recognized as a face Camera1
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

listenStatus = 16
GPIO.setup(listenStatus, GPIO.OUT, initial = 0)

#ปุ่มกดเพื่อ Train ใบหน้า เปนแบบ pull_up
sw_train = 12
GPIO.setup(sw_train, GPIO.IN, pull_up_down = GPIO.PUD_UP)

print('\n\n')
relaypin = [40, 38, 37, 36]  #ขาสำหรับสั่งงาน Relay
Pinidex = 0
for i in relaypin :
    GPIO.setup(relaypin[Pinidex], GPIO.OUT, initial = 0)
    print('\tSutup Relay',Pinidex,'is GPIO pin',relaypin[Pinidex])
    Pinidex += 1
    sleep(0.3)      
print('\n\n')

# Url ของโปรเจค Firebase
url = "https://raspberry-pi-with-fireba-ee139.firebaseio.com/"
firebase = firebase.FirebaseApplication(url)

####################################################################
#ฟังก์ชันเสียงพูดภาษาไทย
def speak(text):
    tts = gTTS(text=text, lang='th')
    filename = 'voice.mp3'
    tts.save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy() == True:
        continue

########################################################################

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

#####################################################################

#ฟังก์ชันการรู้จำใบหน้า
def facerecog_camera1 ():
    id = 0
    names = ''
    prename = ''

    #รับชื่อจาก firebase และแสดงรายชื่อออกที่ Terminal โดยอ่านค่าทุกค่า จาก path ที่ชื่อว่า name 
    names = firebase.get("/name","/")
    prename = names
    print('\n\tName List =>',names)
    print('\n\n')

    Access = firebase.get("/Access to","/")

    #เมื่อเริ่มทำงานให้พูด Starting Programe
    engine = pyttsx3.init()
    volume = engine.getProperty('volume')
    engine.setProperty('volume',1.0)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', 125)
    engine.say('Starting Program')
    engine.runAndWait()
    
    counter = 0
    
    face_id = 0
    Traincount = 0
    id_counter = 1
    sw_status = 0

    firebaseTrain = 'stop'
    firebaseTrain_ID = 0

    ID_Check = 0

    # เลือกโฟลเดอร์ที่เก็บไฟล์ ตรวจจับและ Cap ใบหน้า จากโปรแกรม 01_face_dataset.py
    path = 'dataset'

    while 1:

        if GPIO.input(sw_train) == 0:
            face_id = id_counter
            sw_status = 1
        
        #if firebaseTrain = 'strat' :
            #face_id = firebaseTrain_ID
        
        if sw_status == 1 or firebaseTrain == 'start':  
            print("\n\t[INFO] Initializing face capture. Look the camera and wait ...")  
            
            while 1: 
                ret, img = cam.read()
                img = cv2.flip(img, 1) # Flip vertically
                gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(gray, 1.3, 5) 

                for (x,y,w,h) in faces:

                    cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
                    Traincount += 1
                    print('\tSimple',Traincount)

                    # Save the captured image into the datasets folder
                    cv2.imwrite("dataset/User." + str(face_id) + '.' + str(Traincount) + ".jpg", gray[y:y+h,x:x+w])
                    cv2.putText(img, 'ID :' +str(face_id), (x+10,y-10), font, 1, (0,255,255), 2)
                    cv2.putText(img, 'Simple'+str(Traincount), (x+20,y+h+30), font, 1, (0,255,255), 2)
                    cv2.imshow('camera1',img) 

                k = cv2.waitKey(100) & 0xff # Press 'ESC' for exiting video
                if k == 27:
                    break
                elif Traincount >= 30: # Take 30 face sample and stop video
                    break
                
            sw_status = 0
            id_counter += 1 
            Traincount = 0  

            print ("\n\t[INFO] Training faces. It will take a few seconds. Wait ...")
            faces,ids = getImagesAndLabels(path)
            recognizer.train(faces, np.array(ids))

            # Save โมเดลที่ trainer/trainer.yml
            recognizer.write('trainer/trainer.yml') # recognizer.save() worked on Mac, but not on Pi

            # Print the numer of faces trained and end program
            print("\n\t[INFO] {0} faces trained. Finish".format(len(np.unique(ids))))

        else :
            ret, img =cam.read()
            img = cv2.flip(img, 1) # Flip vertically
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale( 
                gray,
                scaleFactor = 1.2,
                minNeighbors = 5,
                minSize = (int(minW), int(minH)), 
                )
        
            if (faces in faces):           
                for(x,y,w,h) in faces:
                    cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2) #
                    id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
                    # Check if confidence is less them 100 ==> "0" is perfect match 
                    if (confidence < 60):
                        id = names[id]

                    else:
                        id = 'unknown'
                        
                    confidence = "  {0}%".format(round(100 - confidence))
                    cv2.putText(img, str(id), (x+10,y-10), font, 1, (255,0,0), 2)
                    cv2.putText(img, str(confidence), (x+20,y+h+30), font, 1, (255,255,0), 2)
               
            #else:
                    #print('No FaceDetect')
            cv2.namedWindow('camera1',cv2.WINDOW_NORMAL)
            cv2.imshow('camera1',img)
            k = cv2.waitKey(50) & 0xff # Press 'ESC' for exiting video
            if k == 27:
                break

            if id != 'unknown' and id != ID_Check :
                engine.say('Hello'+id)
                engine.runAndWait()
                print('\t\t\t\tHello '+id)
                TimeCheckIn = time.strftime("%A, %d %B %Y, %H:%M:%S")
                firebase.put("/Check_In","ID",id)
                firebase.put("/Check_In","Time",TimeCheckIn)

                index_names = names.index(id)
                j = 0
                for i in Access['name'+str(index_names)] :
                    j += 1
                    if Access['name'+str(index_names)]['relay'+str(j)] == 1 :
                        GPIO.output(relaypin[j-1], 1)
                        print('\tRelay', j-1,'ON')
                    else :
                        print('\tRelay', j-1,'No output')
                
            counter += 1
            if counter == 60:
                ID_Check = 0
                counter = 0           
                '''
                firebaseTrain_ID = firebase.get("/Train","TrainID")
                firebaseTrain = firebase.get("/Train","TrainStatus")

                #มื่อผ่านไประยะเวลาหนิ่ง ให้วนรับชื่อจาก Firebase อีกครั้ง โดยอ่านค่าทุกค่า จาก path ที่ชื่อว่า name 
                names = firebase.get("/name","/")
                if names != prename:
                    #ถ้าชื่อมีการเปลี่ยนแปลงให้แสดงชื่อที่เปลี่ยนแปลงที่ Terminal 
                    print('\t\tChang Names To :',names) 
                    prename = names
                '''
            ID_Check = id

    # Do a bit of cleanup
    print('\n\t[INFO] Exiting Program and cleanup stuff')
    cam.release()
    cv2.destroyAllWindows() 

#####################################################################

AllOff = ['ปิดหมด', 'ปิดทั้งหมด', 'ปิดทุกอย่าง']
SpeakTime = ['กี่โมงแล้ว', 'ตอนนี้กี่โมง', 'ขณะนี้เวลาเท่าไหร่','ตอนนี้เวลาเท่าไหร่', 'ตอนนี้เวลากี่โมง']

# รับค่าคำสั่งเสียงจาก firebase
command_on = firebase.get('/voice command','command on')
command_off = firebase.get('/voice command','command off')

Voice_command_on = []
Voice_command_off = []

j = 0
for i in command_on:
    j += 1
    indexOn =  'relay' + str(j)
    Voice_command_on.append(command_on[indexOn])
j = 0
for i in command_off:
    j += 1
    indexOff =  'relay' + str(j)
    Voice_command_off.append(command_off[indexOff])

print('\tVoice command on list ==>' ,Voice_command_on)
print('\tVoice command off list ==>' ,Voice_command_off)
print('\n\n')

#####################################################################

if __name__ == '__main__':

#มัลติโปรเสซซิ่ง
    #q = mp.Queue()
    p1 = mp.Process(target = facerecog_camera1)
    p1.start()
    sleep(3.3)
    
    #เริ่มคำสั่งเสียง Speech Recognition
    while 1:
        with speech as source:
            GPIO.output(listenStatus, 1)
            print("\tsay something!…")
            audio = r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
            
                
        try:
            recog = r.recognize_google(audio, language = 'th')
            print("\tYou said: " + recog) 
            GPIO.output(listenStatus, 0)

            if recog in Voice_command_on:
                index = Voice_command_on.index(recog)
                GPIO.output(relaypin[index], 1)
                print('\tRelay',index,'ON')
                speak(recog +'เรียบร้อยแล้วค่ะ')   

            if recog in Voice_command_off:
                index = Voice_command_off.index(recog)
                GPIO.output(relaypin[index], 0)
                print('\tRelay',index,'OFF')
                speak(recog +'เรียบร้อยแล้วค่ะ')  
            
            if recog in 'สวัสดี':
                print('\tสวัสดีค่ะมือะไรให้ช่วยมั้ยคะ')
                speak('สวัสดีค่ะมือะไรให้ช่วยมั้ยคะ')  
            
            if recog in SpeakTime :
                thisTime = time.strftime("\tขณะนี้เวลา "+"%H"+" นาฬิกา "+"%M"+" นาที "+"%S"+" วินาทีค่ะ")
                print(thisTime)
                speak(thisTime)
            
            if recog in AllOff :
                Pinindex = 0
                for i in relaypin :
                    GPIO.output(relaypin[Pinindex], 0)
                    Pinindex += 1
                speak('ปิดทุกอย่างเรียบร้อยแล้วค่ะ')

        except sr.UnknownValueError:
            #speak("กรุณาพูดใหม่อีกครั้ง")
            GPIO.output(listenStatus, 0) 
            print("\tกรุณาพูดใหม่อีกครั้ง")
    
        except sr.RequestError as e:
            GPIO.output(listenStatus, 0) 
            speak("การเชื่อมต่อล้มเหลว; {0}".format(e))
            sleep(0.3)
GPIO.cleanup()