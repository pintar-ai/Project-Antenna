#!/usr/bin/python

import sys
import time
import json
import requests
from requests.exceptions import ConnectionError
import serial
from datetime import datetime

import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)
import sys
sys.path.insert(0,"/home/ibrahim/anaconda2/lib/python2.7/site-packages") #because conda messed up PyQt4, so we fetch it directly
from PyQt5 import QtCore, QtGui, uic, QtWidgets

import base64
import cv2
import numpy as np
from fps import FPS

from VideoDetector import VideoInferencePage

from asset_digitization_ui_2 import Ui_Form

from flask import Flask, jsonify, abort, request, make_response, url_for
import gevent
from gevent.pywsgi import WSGIServer

flask_debug = False
shouldrun=False
app = QtWidgets.QApplication( sys.argv )
app.setApplicationName( 'Asset Digitization' )
app.setWindowIcon(QtGui.QIcon('/workspace/client/asset-digitization.png'))

#global parameter for onboard information
var_longitude=""
var_latitude=""
var_gmt=""
var_altitude="0"
var_temperature=""
var_pressure=""
state = "None"
isfirst = False
init_alt = ""
tftime, landingtime = 0,0
baseimageupd = False
sync_flight = False
sync_data = False


#global param for db encrypt
db_key=""

#initiate database
import sqlite3
conn = sqlite3.connect('app_db4.sqlite', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor_main = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS data_table
    (id INTEGER PRIMARY KEY,
    altitude        TEXT    NOT NULL,
    latitude        TEXT    NOT NULL,
    longitude       TEXT    NOT NULL,
    image           TEXT    NOT NULL,
    date_taken      TIMESTAMP    NOT NULL,
    username        TEXT    NOT NULL,
    flight_id       TEXT    NOT NULL,
    sync            BOOLEAN NOT NULL)''')
    conn.commit()

#global param for save PyQt settings
settings = QtCore.QSettings('cairo', 'asset-digitization')
#randomid = settings.value('randomid').toString()
randomid = settings.value('randomid')

#global param for state server IP
server="http://178.128.84.171"
#server="http://127.0.0.1:5100"

#LoRa Server adress
lora_device = "/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_DN03F6YY-if00-port0"

cursor.execute('SELECT *,MAX(flight_id) FROM flight')
entrymaxid = cursor.fetchone()

data = requests.get(server+"/latestID")
jsondata = json.loads(data.text)
idMax = jsondata['flightmax']
dataMax = jsondata['datamax']

print("ID MAX: {}".format(idMax))

print("SERVER : LATEST flight id : {}".format(jsondata['flightmax']))
print("SERVER : LATEST data id : {}".format(jsondata['datamax']))

print ("Test_altitude = {}".format(var_altitude))
print ("Current state is : {}".format(state))
print ("baseimageupd is : {}".format(baseimageupd))


#Create dialog for user login
class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.setWindowTitle("Asset Digitization")
        self.setWindowIcon(QtGui.QIcon('/workspace/client/asset-digitization.png'))
        self.textName = QtWidgets.QLineEdit(self)
        self.textName.setPlaceholderText('Username')
        self.textName.clearFocus()
        self.textPass = QtWidgets.QLineEdit(self)
        self.textPass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.textPass.setPlaceholderText('Password')
        self.textPass.clearFocus()
        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        self.buttonLogin.setFocus()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.textName)
        layout.addWidget(self.textPass)
        layout.addWidget(self.buttonLogin)

    def handleLogin(self):
        if (self.register(self.textName.text(), self.textPass.text())):
            settings.setValue('username', str(self.textName.text()))
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Error', self.message)

    def register(self, username, password):
        global settings
        url = server+"/register"

        payload = "{\n\t\"username\":\"%s\",\n\t\"password\":\"%s\"\n}"%(str(username),str(password))
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'Postman-Token': "2dd5710c-e9b2-4ea5-8015-c6da61a019b9"
            }

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            #print (response)
            if response.status_code==200:
                data = response.json()
                if 'randomid' in data:
                    settings.setValue('randomid', str(data['randomid']))
                    return True
                else :
                    self.message = "Bad user or password"
                    return False
            else :
                self.message = "Bad user or password"
                return False
        except ConnectionError:
            self.message = "Check your network"
            return False
        

# Create a class for our main window
class Main(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        
        # This is always the same
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Sync Thread
        self.netthread=syncThread()
        self.netthread.syncstatus.connect(self.updatesync)
        self.netthread.start()

        #LoRa Stream
        self.lora = loraThread(lora_device)
        self.lora.llh_signal.connect(self.set_llh)
        self.lora.sensor_signal.connect(self.set_sensor)
        self.lora.start()
        
        #Video stream
        #self.video = videoThread("rtmp://localhost/live/stream?liveStreamActive=1")
        #self.video = videoThread("rtmp://localhost/live/stream")
        self.video = videoThread(1)
        self.video.newdetected.connect(self.newdetect)
        self.video.newinv.connect(self.newinventory)
        self.video.newimage.connect(self.set_frame)
        self.video.new_fps.connect(self.set_fps)
        self.video.start()
        
        #self.ui.fps_label.connect(self.video,QtCore.SIGNAL('newFPS(int)'),self.set_fps)

        self.show()

    @QtCore.pyqtSlot(str,str,str)
    def set_llh(self,gmt, lat, lon):
        global var_longitude, var_latitude, var_gmt
        if not flask_debug:
            var_longitude=lon
            var_latitude=lat
            var_gmt=gmt
        else:
            now = datetime.now()
            var_gmt = now.strftime("%H:%M:%S")

        self.ui.longitude_label.setText(var_longitude)
        self.ui.latitude_label.setText(var_latitude)
        self.ui.gmt_label.setText(str(var_gmt))

    @QtCore.pyqtSlot(str,str,str)
    def set_sensor(self,temperature, pressure, altitude):
        global var_altitude, var_temperature, var_pressure
        global state
        global idMax
        global tftime, landingtime
        global baseimageupd
        global isfirst
        global init_alt
        global sync_flight
        global sync_data
        
        #var_altitude=10
        if not flask_debug:
            var_pressure=pressure
            var_temperature=temperature
            var_altitude=altitude
            print (type(var_altitude))
            
            '''
            if isfirst == False:
                init_alt = var_altitude
                var_altitude = 0
                isfirst = True
            else:
                var_altitude = float(var_altitude) - float(init_alt)
                print (var_altitude)
                print (type(var_altitude))
            '''

        #print (float(var_altitude))
        #print (type(var_altitude))

        print ("Test_altitude = {}".format(var_altitude))
        print ("Current state is : {}".format(state))
        print ("baseimageupd is : {}".format(baseimageupd))

        if state =="None" and float(var_altitude)>=10:
            #print ("hahah1")
            #print ("Test_altitude = {}".format(var_altitude))
            #print ("Current state is : {}".format(state))
            state = "take_off"
            now = datetime.now()
            tftime = now.strftime("%H:%M:%S")
        
        elif state == "take_off" and float(var_altitude) == 0:
            state = "None"
            isfirst = False
            now = datetime.now()
            baseimageupd = False
            landingtime = now.strftime("%H:%M:%S")
            cursor_main.execute("""UPDATE flight SET landing=? WHERE flight_id=?""",(landingtime,idMax))
            conn.commit()
            #landingtime = str(0)
            time.sleep(2)
            sync_flight = True
            sync_data = True
        

        #self.ui.altitude_label.setText(altitude+" m")
        self.ui.altitude_label.setText(str(var_altitude)+" m")
        self.ui.temperature_label.setText(var_temperature+" C")
        self.ui.pressure_label.setText(var_pressure+" mbar")

    def set_frame(self,frame):
        pixmap = QtGui.QPixmap.fromImage(frame)
        self.ui.video_label.setPixmap(pixmap)

    def set_fps(self,fps):
        self.ui.fps_label.setText(str(fps))

    @QtCore.pyqtSlot(str)
    def newdetect(self,image):
        if not (var_altitude and var_longitude and var_latitude):
            print ("you need to connected with LoRa before start to detect")
            return
        date_taken = datetime.now().replace(second=0, microsecond=0)
        print (date_taken)
        username = str(settings.value('username'))
        takeofftime = str(tftime)
        landtime = str(landingtime)
        sync=False
        image = str(image)
        global baseimageupd, idMax
        idMax = int(idMax) + 1
        print ("\n\n\n\n\n\n====================")
        print ("====================")
        print ("====================")
        print ("NEW IMAGE UPDATED --")
        print (username)
        print (takeofftime) 
        print (landtime)
        print("Insert to FLIGHT ID : {}".format(idMax))
        print (sync)
        print ("====================")
        print ("====================")
        print ("====================\n\n\n\n\n\n")

        try:
            cursor_main.execute('INSERT INTO flight (altitude,latitude,longitude,loc_image,date_taken,takeoff,landing,username,sync,flight_id) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (var_altitude, var_latitude, var_longitude, image, date_taken, takeofftime, landtime, username, sync, idMax))
            conn.commit()
            print("DAH MASUK DB")
            baseimageupd = True
        except Exception as e:
            print (e.message)

    @QtCore.pyqtSlot(str,str)
    def newinventory(self,image,label):

        if not (var_altitude and var_longitude and var_latitude):
            print ("you need to connected with LoRa before start to detect")
            return
        label = str(label)
        date_taken = datetime.now().replace(second=0, microsecond=0)
        username = str(settings.value('username'))
        sync=False #false
        image = str(image)

        global idMax
        global dataMax
        dataMax = dataMax + 1
        #idflight = int(idMax) + 1

        
        
        print ("\n\n\n\n\n\n====================")
        print ("====================")
        print ("====================")
        print ("NEW INV IMAGE UPDATED --")
        print (username)
        print (date_taken)
        print (var_altitude)
        print (label)
        print("Insert FLIGHT ID : {}".format(idMax))
        print("INSERT DATA ID : {}".format(dataMax))
        print ("====================")
        print ("====================")
        print ("====================\n\n\n\n\n\n")
        print("DAH MASUK DB")
        

        try:
            cursor_main.execute('INSERT INTO data_table (id, flight_id, altitude,latitude,longitude,image,date_taken,username,type,sync) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (dataMax,idMax, var_altitude, var_latitude, var_longitude, image, date_taken, username,label,sync))
            conn.commit()
        except Exception as e:
            print (e.message)

    @QtCore.pyqtSlot(str)
    def updatesync(self,data):
        print ("sync_data : {}".format(data))
        self.ui.sync_label.setText("SYNC "+data)

    def closeEvent(self, event):
        global shouldrun
        shouldrun=False

class syncThread(QtCore.QThread):
    syncstatus = QtCore.pyqtSignal(str)

    def __init__(self):
        super(syncThread,self).__init__()
        self.url = server+"/insert"
        self.url2 = server+"/insert2"

    def run(self):
        global sync_flight
        #global sync_data

        print ("sync worker start syncing")
        if noconnection:
            print ("sync worker cant connect to server")
        if not shouldrun:
            print ("sync worker forbiden to run")
        while shouldrun and not noconnection:

            print ("sync local to server START HERE!")
            #calculate total data in DB

            #print ("sync_flight : {}".format(sync_flight))
            
            cursor.execute('SELECT * FROM flight')
            entryf1 = cursor.fetchall()
            total=len(entryf1)
            #conn.commit()

            cursor.execute('SELECT * FROM flight WHERE NOT sync')
            entryf2 = cursor.fetchall()
            notuploaded=len(entryf2)
            #conn.commit()

            data = str(total-notuploaded)+'/'+str(total)
            self.syncstatus.emit(data)

            

            #print ("UPDATE sync status = "+data)

            #calculate total data in DB
            cursor.execute('SELECT * FROM data_table')
            entryd1 = cursor.fetchall()
            total1=len(entryd1)

            cursor.execute('SELECT * FROM data_table WHERE NOT sync')
            entryd2 = cursor.fetchall()
            notuploaded1=len(entryd2)
            

            print ("UPDATE sync status FLIGHT TABLE = "+str(total-notuploaded)+'/'+str(total))
            print ("UPDATE sync status DATA_TABLE TABLE = "+str(total1-notuploaded1)+'/'+str(total1))

            if sync_flight != True:
                #print ("Waiting for drone to landing")
                continue

            if entryf2 is None:
                print("Entry flight is NONE")
                time.sleep(15)#try to sync every 30 second
            elif not entryf2:
                print("Not flight entry")
                time.sleep(15)#try to sync every 30 second
            else :
                print("YES ENTRY flight NEED TO UPDATE!")
                for row in entryf2:
                    altitude = row['altitude']
                    latitude = row['latitude']
                    longitude = row['longitude']
                    date_taken = row['date_taken']
                    image = row['loc_image']
                    takeoff = row['takeoff']
                    landing = row['landing']
                    username = row['username']
                    id = row['flight_id']

                    #if takeoff == str(0) or landing == str(0):
                    #if sync_flight != True:
                        #continue

                    payload = "{\n\"altitude\":\"%s\",\n\"latitude\":\"%s\",\n\"longitude\":\"%s\",\n\"date_taken\":\"%s\",\n\"image\":\"%s\",\n\"username\":\"%s\",\n\"landing\":\"%s\",\n\"takeoff\":\"%s\",\n\"flight_id\":\"%s\"\n}"%(str(altitude),str(latitude),str(longitude),str(date_taken),str(image),str(username),str(landing),str(takeoff),str(id))
                    print ("Flight payload : {}".format(payload))
                    if self.upload(payload):
                        try :
                            cursor.execute("""UPDATE flight SET sync=? WHERE flight_id=?""",(True,id))
                            conn.commit()

                        except Exception as e:
                            print (e.message)
                    else : print("cannot update sync flight table")


            if entryd2 is None:
                print("Entry data table is NONE")
                time.sleep(15)#try to sync every 30 second
            elif not entryd2:
                print("Not data table entry")
                time.sleep(15)#try to sync every 30 second
            else :
                print("YES ENTRY data table NEED TO UPDATE!")
                for row in entryd2:
                    altitude = row['altitude']
                    latitude = row['latitude']
                    longitude = row['longitude']
                    date_taken = row['date_taken']
                    image = row['image']
                    username = row['username']
                    type = row['type']
                    flight_id = row['flight_id']
                    id = row['id']

                    #if sync_data != True:
                        #continue

                    payload = "{\n\"altitude\":\"%s\",\n\"latitude\":\"%s\",\n\"longitude\":\"%s\",\n\"date_taken\":\"%s\",\n\"image\":\"%s\",\n\"username\":\"%s\",\n\"type\":\"%s\",\n\"flight_id\":\"%s\",\n\"id\":\"%s\"\n}"%(str(altitude),str(latitude),str(longitude),str(date_taken),str(image),str(username),str(type),str(flight_id),str(id))
                    if self.upload2(payload):
                        try :
                            cursor.execute("""UPDATE data_table SET sync=? WHERE id=?""",(True,id))
                            conn.commit()
                        except Exception as e:
                            print (e.message)
                    else : print("cannot update sync data table")
        
            sync_flight = False
            #sync_data = False

    def upload(self, payload):
        url = self.url
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
            }

        response = requests.request("POST", url, data=payload, headers=headers)
        data = response.json()

        if 'status' in data:
            print(data)
            print("Yes update flight to server")
            return True
        else :
            print(data)
            print("CANNOT flight update to server")
            return False

    def upload2(self, payload):
        url2 = self.url2
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
            }

        response = requests.request("POST", url2, data=payload, headers=headers)
        data = response.json()
        if 'status' in data:
            print(data)
            print("Yes update data to server")
            return True
        else :
            print(data)
            print("CANNOT data update to server")
            return False


class videoThread(QtCore.QThread):
    newdetected = QtCore.pyqtSignal(str)
    newinv = QtCore.pyqtSignal(str,str)
    newimage = QtCore.pyqtSignal(QtGui.QImage)
    new_fps = QtCore.pyqtSignal(int)

    def __init__(self,address):
        super(videoThread,self).__init__()
        self.video_address = address

    def image_resize(self,image, width = None, height = None, inter = cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation = inter)

        # return the resized image
        return resized

    def run(self):
        #Activate Detector module
        self.detector = VideoInferencePage()

        # Create a VideoCapture object and read from input file
        # If the input is the camera, pass 0 instead of the video file name
        cap = cv2.VideoCapture(self.video_address)
        fps = None
        new_detected=[]
        # Check if camera opened successfully
        if (cap.isOpened()== False): 
            print("Error opening video stream or file")
         
        # Read until video is completed
        while(cap.isOpened() or shouldrun):
            # Capture frame-by-frame
            ret, frame = cap.read()
            global baseimageupd
            if ret == True:
                if not self.detector.isready():
                    continue
                if not fps:
                    fps = FPS().start()
                elif fps.elapsed()>60:
                    fps = FPS().start()


                if state=="take_off" and float(var_altitude) >= 10 and baseimageupd==False:
                    #print ("hahah2")
                    object_image = frame
                    baseimageupd = True
                    #cv2.imwrite("/media/ibrahim/Data/faster-rcnn/tools/img/baseimage.jpg",object_image)
                    image = self.image_resize(object_image, height=300)
                    retval, buffer = cv2.imencode('.png', image)
                    #print ("hahah22")
                    image_base64 = base64.b64encode(buffer)
                    self.newdetected.emit(image_base64)
                    #print ("hahah23")

                #feed the detector and wait for true result
                self.detector.send_frame(frame)
                result=self.detector.get_result()
                
                #Uncomment this if want to bypass the detector
                #result=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if not isinstance(result, np.ndarray):
                    continue

                # Display the resulting frame
                convertToQtFormat = QtGui.QImage(result.data, result.shape[1], result.shape[0], QtGui.QImage.Format_RGB888)
                p = convertToQtFormat.scaled(1260, 720, QtCore.Qt.KeepAspectRatio)
                self.newimage.emit(p)
                
                #self.emit(QtCore.SIGNAL('newFPS(int)'), int(fps.fps()))

                passobject = self.detector.get_passingobject()
                #passobject = []
                if len(new_detected)<len(passobject):
                    for objectID in passobject.keys():
                        if not objectID in new_detected:
                            new_detected.append(objectID)
                            #image parsing to base64
                            #print (passobject[objectID]['image'])

                            try:
                                image = self.image_resize(passobject[objectID]['image'], height=300)
                                label = (passobject[objectID]['label'])
                                retval, buffer = cv2.imencode('.png', image)
                                image_base64 = base64.b64encode(buffer)
                                self.newinv.emit(image_base64, label)
                            except Exception as e:
                                print ("\n*************\nMissing Image\n***************\n")
                                continue

                            '''    
                            if passobject[objectID]['image'] != []:
                                image = self.image_resize(passobject[objectID]['image'], height=300)
                                label = (passobject[objectID]['label'])
                                retval, buffer = cv2.imencode('.png', image)
                                image_base64 = base64.b64encode(buffer)
                                self.newinv.emit(image_base64, label)
                            else:
                                print ("\n*************\nMissing Image\n***************\n")
                                continue
                            '''

                fps.update()
                self.new_fps.emit(int(fps.fps()))
                if self.detector.isobjectsupdated:
                    objects = self.detector.get_objects()

                    
                # Press Q on keyboard to  exit
                if not shouldrun:
                    fps.stop()
                    self.detector.exit_detection()
                    break
         
            # restart stream
            else: 
                print ("ret is false")
                if fps:
                    fps.stop()
                time.sleep(3)
                cap.release()
                cap = cv2.VideoCapture(self.video_address)
                if (cap.isOpened()== True) and fps: 
                    fps.start()
         
        # When everything done, release the video capture object
        cap.release()
         
        # Closes all the frames
        cv2.destroyAllWindows()
        
class loraThread(QtCore.QThread):
    llh_signal = QtCore.pyqtSignal(str,str,str)
    sensor_signal = QtCore.pyqtSignal(str,str,str)


    def __init__(self,device_address):
        super(loraThread,self).__init__()
        self.device_address = device_address

    def run(self):
        serial_found=False
        

        while shouldrun :
            msg=""
            if flask_debug: # emit empty data, it will replaced by global var
                self.llh_signal.emit('0','0','0')
                self.sensor_signal.emit('0','0','0')
                time.sleep(2) # update every 2 seconds
                continue

            
            try:
                if not serial_found:
                    ard = serial.Serial(self.device_address,9600,timeout=5)
                    serial_found=True
                else:
                    msg = ard.readline()
            except:
                serial_found=False
                print("Cannot found LoRa Server in address : "+self.device_address)
                sleeping=10
                print("wait for %s second for reconnect with LoRa"%str(sleeping))
                time.sleep(sleeping)
                continue
            
            msg = msg.replace(" ", "")
            msg = msg.replace('"', "")
            data = msg.split()
            
            if len(data)>0:
                if "llh:" in data[0]:
                    llh = data[0].split("llh:")
                    llh = llh[1].split(",")
                    if len(llh) != 4:
                        continue
                    gmt = llh[0]
                    latitude = llh[1]
                    longitude = llh[2]
                    self.llh_signal.emit(gmt,latitude,longitude)
                if "sensors:" in data[0]:
                    sensor = data[0].split("sensors:")
                    sensor = sensor[1].split(",")
                    if len(sensor) != 3:
                        continue
                    temperature = sensor[0]
                    pressure = sensor[1]
                    altitude = sensor[2]

                    self.sensor_signal.emit(temperature,pressure,altitude)
   
def validate(randomid):
        if not randomid:
            return False
        url = server+"/validate"
        
        payload = "{\n\t\"randomid\":\"%s\"\n}"%(str(randomid))
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
            }

        response = requests.request("POST", url, data=payload, headers=headers)
        #print ("test res {}".format(response))
        data = response.json()
        if 'registered' in data:
            return True
        else :
            return False

def mainloop(app):
    while shouldrun:
        app.processEvents()
        while app.hasPendingEvents():
            if not shouldrun:
                break
            app.processEvents()
            gevent.sleep()
        gevent.sleep() # don't appear to get here but cooperate again
    print("mainloop is closing")
    goodbye()

   
if __name__ == "__main__":
    fapp = Flask(__name__)
    fapp.debug=True

    @fapp.route("/debug", methods=['POST'])
    def debug():
        if not request.json or not 'debug' in request.json:
            abort(400)
        global flask_debug
        flask_debug = request.json['debug']
        return jsonify({'status': 'received'}), 201

    @fapp.route('/llh', methods=['POST'])
    def replace_llh():
        if not request.json or not 'longitude' or not 'latitude' in request.json:
            abort(400)
        global var_longitude, var_latitude
        var_longitude = request.json['longitude']
        var_latitude = request.json['latitude']
        return jsonify({'status': 'received'}), 201

    @fapp.route('/sensors', methods=['POST'])
    def replace_sensors():
        if not request.json or not 'altitude' or not 'temperature' or not 'pressure' in request.json:
            abort(400)
        global var_altitude, var_temperature, var_pressure
        var_altitude = request.json['altitude']
        var_temperature = request.json['temperature']
        var_pressure = request.json['pressure']
        return jsonify({'status': 'received'}), 201

    def goodbye():
        print("killing webserver")
        f.kill(block=False)
        print("is webserver alive? ", f.dead)

    def openmainwindow():
        http_server = WSGIServer(('0.0.0.0', 8000), fapp)
        app.setApplicationName( 'Drone Client' )
        window = Main()
        window.show()
        # connection
        app.lastWindowClosed.connect(app.quit)


        shouldrun=True
        f = gevent.spawn(http_server.serve_forever)
        g = gevent.spawn(mainloop, app)
        gevent.joinall([f, g])

    http_server = WSGIServer(('0.0.0.0', 8000), fapp)
    init_db()
    login = Login()
    isvalid = False
    noconnection = False
    try:
        isvalid = validate(randomid)
    except ConnectionError:
        if randomid:
            noconnection = True
    if isvalid or noconnection or login.exec_() == QtWidgets.QDialog.Accepted:
        init_db()
        shouldrun=True
        window = Main()
        window.show()

        #QtCore.QObject.connect( app, QtCore.SIGNAL( 'lastWindowClosed()' ), app, QtCore.SLOT( 'quit()' ) )
        app.lastWindowClosed.connect(app.quit)
        # execute application
        f = gevent.spawn(http_server.serve_forever)
        g = gevent.spawn(mainloop, app)
        gevent.joinall([f, g])