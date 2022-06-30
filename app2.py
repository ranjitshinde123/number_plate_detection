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
                        from datetime import datetime

                        t1 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        try:
                            mycursor = mydb.cursor()
                            sql = "Update parking set exit_time= %s WHERE num_plate = %s "
                            tup=(t1,text)
                            mycursor.execute(sql,tup)
                            mydb.commit()
                            print(mycursor.rowcount, "record inserted.")
                            pyttsx3.speak("number plate save successfully")
                        except:
                            print("number plate is alredy exits")
                            pyttsx3.speak("number plate is alredy exits")
                        try:
                            cur = mydb.cursor()
                            query = "SELECT entry_time,exit_time FROM parking WHERE num_plate=%s"
                            tup=(text,)
                            cur.execute(query,tup)
                            data = cur.fetchall()
                            t1=data[0][0]
                            t2=data[0][1]
                            mydb.commit()
                            tt = t2 - t1
                            print('Total time parking used :', tt)
                            ttm = int(tt.total_seconds() / 60)
                            fees = (ttm // 60) * 20
                            if ttm % 60 > 30:
                                fees += 10
                            else:
                                fees+=20
                            if ttm // 60 == 0:
                                fees = 20
                            mycursor = mydb.cursor()
                            sql = "Update parking set total_time=%s, fees=%s WHERE num_plate=%s"
                            tup = (ttm, fees,text)
                            mycursor.execute(sql, tup)
                            mydb.commit()
                            print('total parking fees are :',fees)
                        except:
                            print('data not found')

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
    # app.run(debug=True)
    app.run('localhost',5001)