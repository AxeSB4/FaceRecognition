# -*- coding: utf-8 -*-

import numpy as np
import os 
import pyttsx3
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

print('\n\n')
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

listenStatus = 16
GPIO.setup(listenStatus, GPIO.OUT, initial = 0)


relayPin = [40, 38, 37, 36]  #ข าสำหรับสั่งงาน Relay
Pinindex = 0
for i in relayPin :
    #Relay Active LOW จึงตั้งค่าเริ่มต้นให้เป็น 1
    GPIO.setup(relayPin[Pinindex], GPIO.OUT, initial = 0)
    print('Sutup Relay',Pinindex,'is GPIO pin',relayPin[Pinindex])
    Pinindex += 1
    sleep(0.3)      
print('\n\n')

# url ของโปรเจค Firebase
url = "https://raspberry-pi-with-fireba-ee139.firebaseio.com/"
firebase = firebase.FirebaseApplication(url)

########################################################################
# ฟังก์ชันเสียงพูดภาษาไทย
def speak(text):
    tts = gTTS(text=text, lang='th')
    filename = 'voice.mp3'
    tts.save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy() == True:
        continue

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

print('Voice command on list ==>' ,Voice_command_on)
print('Voice command off list ==>' ,Voice_command_off)
print('\n\n')


######################################################################
#เริ่มคำสั่งเสียง Speech Recognition
while 1:
    with speech as source:
        GPIO.output(listenStatus, 1)
        print("say something!…")
        audio = r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        
            
    try:
        recog = r.recognize_google(audio, language = 'th')
        print("You said: " + recog) 
        GPIO.output(listenStatus, 0)

        if recog in Voice_command_on:
            index = Voice_command_on.index(recog)
            GPIO.output(relayPin[index], 1)
            print('Relay',index,'ON')
            speak(recog +'เรียบร้อยแล้วค่ะ')   

        if recog in Voice_command_off:
            index = Voice_command_off.index(recog)
            GPIO.output(relayPin[index], 0)
            print('Relay',index,'OFF')
            speak(recog +'เรียบร้อยแล้วค่ะ')  
        
        if recog in 'สวัสดี':
            print('สวัสดีค่ะมือะไรให้ช่วยมั้ยคะ')
            speak('สวัสดีค่ะมือะไรให้ช่วยมั้ยคะ')  
        
        if recog in SpeakTime :
            thisTime = time.strftime("ขณะนี้เวลา "+"%H"+" นาฬิกา "+"%M"+" นาที "+"%S"+" วินาทีค่ะ")
            print(thisTime)
            speak(thisTime)
        
        if recog in AllOff :
            Pinindex = 0
            for i in relayPin :
                GPIO.output(relayPin[Pinindex], 0)
                Pinindex += 1
            speak('ปิดทุกอย่างเรียบร้อยแล้วค่ะ')

    except sr.UnknownValueError:
        #speak("กรุณาพูดใหม่อีกครั้ง")
        GPIO.output(listenStatus, 0) 
        print("กรุณาพูดใหม่อีกครั้ง")
 
    except sr.RequestError as e:
        speak("การเชื่อมต่อล้มเหลว; {0}".format(e))
        sleep(0.3)

GPIO.cleanup() 
