from firebase import firebase

url = "https://raspberry-pi-with-fireba-ee139.firebaseio.com/"
firebase = firebase.FirebaseApplication(url)
statut = firebase.get("/voice command","command on") #firebase.put("/Test","vall",9999)
print('Status =>',statut)

