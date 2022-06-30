import cv2
import re
import pytesseract
from flask import Response, render_template, Flask
import pyttsx3
import mysql.connector

app = Flask(__name__)
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="parking"
)

camera=cv2.VideoCapture(0)
s=set()
def gen_frames():  # generate frame by frame from camera
    pytesseract.pytesseract.tesseract_cmd = r'C:\Users\DELL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
    plateCascade = cv2.CascadeClassifier("numberplate.xml")
    minArea = 500
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # out = cv2.VideoWriter('output2.mp4', fourcc, 20.0, (640, 480))
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        imgGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        numberPlates = plateCascade.detectMultiScale(imgGray, 1.1, 4)
        for (x, y, w, h) in numberPlates:
            area = w * h
            if area > minArea:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                imgRoi = frame[y:y + h, x:x + w]
                return_value, image = camera.read()
                # out.write(frame)
                text1 = pytesseract.image_to_string(imgRoi,lang='eng', config='--oem 3 ,-l eng ,--psm 6 ,-c tessedit_char_whitelist = ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                text = "".join(text1.split()).replace(":", "").replace("-", "").replace(";","")
                text = str(text).strip()

                # cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                m = re.search('[A-Z]{2}\s*[0-9]{1,2}\s*[A-Z]{2}\s*[0-9]{1,4}',
                              text)  # cheching text using regular expression with numberplate formate
                if m:
                    cv2.putText(frame, 'ok', (x, y - 15), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    text = str(m.group(0))
                    n = re.fullmatch('[A-Z]{2}\s*[0-9]{1,2}\s*[A-Z]{2}\s*\d{1,4}', text)
                    if n and text not in s:
                        s.add(text)
                        cv2.putText(frame, "NumberPlate", (x, y - 5), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                        print('text found in number plate formate:', text)
                        print(text)
                        img_name = "pics/"+text+".png"
                        cv2.imwrite(img_name, imgRoi)
                        print('image saved')
                        pyttsx3.speak('Number plate detected successfully')
                        pyttsx3.speak("number plate is the something went wrong ")
                        from datetime import datetime
                        try:
                            t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            mycursor = mydb.cursor()
                            sql = "INSERT INTO parking (num_plate ,entry_time) VALUES (%s,%s)"
                            val = (text,t)
                            mycursor.execute(sql, val)
                            mydb.commit()
                            print(mycursor.rowcount, "record inserted.")
                            pyttsx3.speak("number plate save successfully")
                            # pyttsx3.speak("record inserted into database")
                        except:
                            print("number plate is alredy exits")
                            pyttsx3.speak("number plate is alredy exits")

        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/video_feed')
def video_feed():
    while True:
        success, img = camera.read()
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

