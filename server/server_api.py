#!/usr/bin/env python
from flask import Flask, jsonify, session, abort, request, make_response, url_for, render_template, redirect, flash
from gevent.pywsgi import WSGIServer
from datetime import datetime, timedelta
import signal
import sys
import os
import string
import configparser
import random 
import string
import json
import requests
import math
import re
import sys
import numpy as np
import uuid
#from pyproj import Proj, transform
#import logging


app = Flask(__name__, static_url_path='/static')

#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)

config = configparser.ConfigParser()
config.read('/media/ibrahim/Data/perceptron-server/config.ini')
app.secret_key = config['GENERAL']['SECRET_KEY']

import sqlite3

# if database isn't exist, then create one with random filename
import uuid
if not config['GENERAL']['SQLITE_PATH'] or not os.path.exists(config['GENERAL']['SQLITE_PATH']):
    
    uuid = str(uuid.uuid4()).split('-')[0]
    config['GENERAL']['SQLITE_PATH'] = "db_{}.sqlite".format(uuid)

    # write new sqlite filename inside our config
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

conn = sqlite3.connect(config['GENERAL']['SQLITE_PATH'], check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

import flask_login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

time_limit = ""

class User(flask_login.UserMixin):
    pass

def changeAntenna (antype):

    if antype == "antenna1":
        antenna = "Antenna 1"
    elif antype == "antenna2":
        antenna = "Antenna 2"
    elif antype == "antenna3":
        antenna = "Antenna 3"
    elif antype == "antenna4":
        antenna = "Antenna 4"
    else:
        antenna = "Antenna 5"
    return antenna

def remove_dirty_form(dirtylist,number=False):
    dirtylist=dirtylist.replace(']', '')
    dirtylist=dirtylist.replace('[', '')

    splitlist = dirtylist.split (',')
    for index,value in enumerate(splitlist):
        if len(value)<=0:
            continue
        value=value.strip()
        if value[0]=='u':
            value=value[1:]
        value=value.replace("'", "")
        if number:
            value=re.sub("[A-Za-z]","",value)
        splitlist[index]=value
    return splitlist



@login_manager.user_loader
def user_loader(username):
    print ("user_loader = {}".format(username))
    lock.acquire(True)
    cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
    lock.release()
  
    entry = cursor.fetchone()

    if entry is None:
        print("user_loader24")
        return
    else :
        user = User()
        user.id = username
        print("user_loader13 = {}".format(user.id))
        return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    print("request_loader = {}".format(username))
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry is None:
        print("request_loader24")
        return
    elif request.form['password'] != entry['password']:
        print("request_loader2")
        redirect(url_for('login'))
    else :
        user = User()
        user.id = username
        print("request_loader3 = {}".format(user.id))
        user.is_authenticated = request.form['password'] == entry['password']

        return user



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'GET':
        print("hahah789")
        return render_template('dash/login_page.html')

    username = request.form['username']
    print("login = {}".format(username))

    randomid = id_generator()
    cursor.execute("""UPDATE user_table SET status_log=? WHERE username=?""",(randomid,username))
    conn.commit()

    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    #global time_limit

    if entry :
        if request.form['password'] == entry['password']:
            user = User()
            user.id = randomid
            print (user.id)
            flask_login.login_user(user)
            #if entry['status_log']==True:
                #error = 'This username still in session !'
            #else:
                #date_now = datetime.now()
            
            if entry['privilage']==7:
                flash('You were successfully logged in')
                
                #time_limit = (date_now + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
                #print (time_limit)
                return redirect(url_for('show_admin'))
            flash('You were successfully logged in as user')
            #cursor.execute("""UPDATE user_table SET status_log=? WHERE username=?""",(randomid,username))
            #conn.commit()
            return redirect(url_for('show_map'))
        else:
            error = 'Wrong Username or Password. Try again!'
    
    print("hahah456")
    return render_template('dash/login_page.html', error=error)

@app.route('/loginadmin', methods=['GET', 'POST'])
def loginadmin():
    if request.method == 'GET':
        return render_template('dash/adminlogin.html')
        return '''
               <form action='login' method='POST'>
                <input type='text' name='username' id='username' placeholder='username'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    username = request.form['username']
    print("loginadmin = {}".format(username))
    
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if request.form['password'] == entry['password']:
            user = User()
            user.id = entry['status_log']
            flask_login.login_user(user)
            if entry['privilage']==7:
                flash('You were successfully logged in')
                return redirect(url_for('show_admin'))
            return ("Wrong")

    return redirect(url_for('loginadmin'))


#Render template for template

@app.route('/regtemplate')
def regtemplate():
    None
    return render_template('dash/register.html')

@app.route('/adminlogin')
def adminlogin():
    None
    return render_template('dash/adminlogin.html')

@app.route('/userlogin')
def userlogin():
    None
    print ("hahah123")
    return render_template('dash/login_page.html')

# END OF render template for template

def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@app.route('/register', methods=['POST'])
def register():
    if not request.json or not 'username' or not 'password' in request.json:
        abort(400)

    username = request.json['username']
    password = request.json['password']
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry :
        if password == entry['password']:
            randomid=id_generator()
            cursor.execute('UPDATE user_table SET randomid = ? WHERE username= ? ',(randomid,username))
            conn.commit()
            return jsonify({'randomid': randomid}), 200
        else :
            abort(400, " wrong password")
    else :
        abort(400, " username was not registered")


@app.route('/validate', methods=['POST'])
def validate():
    if not request.json or not 'randomid' in request.json:
        abort(400)

    randomid = request.json['randomid']
    cursor.execute('SELECT * FROM user_table WHERE randomid=? ', (randomid,))
    entry = cursor.fetchone()

    if entry :
        return jsonify({'registered': 'true'}), 200
    else :
        abort(400, " username was not registered")



@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id

'''
@app.before_request
def before_request():
    print ("test1")
    if flask_login.current_user.is_authenticated:
        time_now_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print ("hahahah12123")
        print (time_now_end)
        print (time_limit)
        
        if time_now_end > time_limit:
            return redirect(url_for('logout'))
    else:
        login()

    #username = flask_login.current_user.id
    #print (username)
    #print ("hahahah12123")
    #cursor.execute("""UPDATE user_table SET status_log=? WHERE username=?""",(False,username))
    #conn.commit()
    #session.permanent = True
    #app.permanent_session_lifetime = timedelta(minutes=1)
    #session.modified = True
'''
@app.route('/logout')
def logout():
    
    #username = flask_login.current_user.id
    #cursor.execute("""UPDATE user_table SET status_log=? WHERE username=?""",(False,username))
    #conn.commit()
    flask_login.logout_user()
    return redirect(url_for('login'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))
    #return 'Unauthorized'

@auth.get_password
def get_password(username):
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()

    if entry is None:
        return None
    else :
        return entry['password']

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_table
    (username   TEXT    PRIMARY KEY,
    password    TEXT    NOT NULL,
    privilage   INT     NOT NULL,
    randomid    TEXT,
    enabled     BOOLEAN NOT NULL,
    status_log     TEXT,
    date_created    TIMESTAMP   NOT NULL)''')      

    #insert root account to add, edit and remove user. 
    cursor.execute('SELECT * FROM user_table WHERE username=? ', ('root',))
    entry = cursor.fetchone()

    if entry is None:
        cursor.execute('INSERT INTO user_table (username,password,privilage,enabled,date_created) VALUES (?,?,?,?,?)', ('root', 'root', '7', True, datetime.today().strftime('%Y-%m-%d')))

    cursor.execute('''CREATE TABLE IF NOT EXISTS data_table
    (id INTEGER PRIMARY KEY,
    altitude        TEXT    NOT NULL,
    latitude        TEXT    NOT NULL,
    longitude       TEXT    NOT NULL,
    image           TEXT    NOT NULL,
    date_taken      TIMESTAMP    NOT NULL,
    username        TEXT    NOT NULL,
    FOREIGN KEY (username) REFERENCES user_table (username))''')
    conn.commit()

user_request = {}

@app.route('/')
def index():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        print ("index = {}".format(username))
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                return render_template('dash/adminboard.html')
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/pushadmin', methods=['GET'])
@flask_login.login_required
def pushadmin():
    datel = []
    if flask_login.current_user.is_authenticated:
        date = request.args.get('date')
        date = str(date)
        print(date)
        username = flask_login.current_user.id
        datel.append(date)
        global user_request


    #start
    print("this is date {}".format(date))
    cursor.execute('SELECT * FROM flight WHERE date_taken LIKE ?', (date+"%",))
    entry = cursor.fetchall()

    if entry:
        print("YES MATCH!")
        x=1
        marker={}
        lat = []
        lon = []
        dates = []
        dates2 = []
        img=[]
        total_row=len(entry)
        timetakeoff =[]
        timelanding = []

        for row in entry:
            print("enter here 2nd row")
            print("date matching : {}".format(row['date_taken']))
            imginv = []
            latinv = []
            loninv = []
            antypelist = []
            altinv = []
            
            flight_id = row['flight_id']
            print(flight_id)
            altitude = row['altitude']
            latitude = row['latitude']
            longitude = row['longitude']
            date_taken = row['date_taken']
            user= row['username']
            image = row['loc_image']
            takeoff = row['takeoff']
            landing = row['landing']
            role = 0
            takeoff = (datetime.strptime(takeoff,'%H:%M:%S').time())
            landing = (datetime.strptime(landing,'%H:%M:%S').time())

            img.append(image)
            lat.append(float(row['latitude']))
            lon.append(float(row['longitude']))
            dates.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))
            dates2.append(str(datetime.strptime(date_taken, '%Y-%m-%d %H:%M:%S').strftime('X%d-X%m-%Y').replace('X0','X').replace('X','')))

            cursor.execute('SELECT * FROM data_table WHERE flight_id=?', (flight_id,))
            entry2 = cursor.fetchall()
            
            for i in entry2:
                print("enter 3rd row")
                
                #append data inv table
                image2 = i['image']
                lati = i['latitude']
                user2= i['username']
                loni = i['longitude']
                antype = i['type']
                alt = i['altitude']

                antenna = changeAntenna(antype) #change antenna name

                latinv.append(lati)
                loninv.append(loni)
                imginv.append(image2)
                antypelist.append(antenna)
                altinv.append(alt)

            print("all altitude : {}".format(altinv))

            

            #description = '<b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+'</span> ]</b><br><br><b>Lon/Lat : </b>'+str(longitude)+'&#176 , '+str(latitude)+'&#176'+'<br><b>Date/Time : </b>'+str(date_taken)+'<br><br><center><b>Fieldwork View </b><br><br>'+'<img style="height: 60%; width: 60%;" src="data:image/png;base64,'+str(image)+'" ismap /></center><br><form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;"><input type="hidden" value="'+str(imginv)+'" name="imginv"><input type="hidden" value="'+str(loninv)+'" name="loninv"> <input type="hidden" value="'+str(latinv)+'" name="latinv"> <input type="hidden" value="'+str(altinv)+'" name="altinv"> <input type="hidden" value="'+str(date_taken)+'" name="date"><input type="hidden" value="'+image+'" name="imag"> <input type="hidden" value="'+str(takeoff)+'" name="takeoff"><input type="hidden" value="'+str(landing)+'" name="landing"><input type="hidden" value="'+str(role)+'" name="role"> <input type="hidden" value="'+str(antypelist)+'" name="antypelist"> <input type="hidden" value="'+str(flight_id)+'" name="flightid"> <input style="width:50%;" type="submit" value="More Info"> </form>'
            #description = 'kentang'
            description = ( '<center><b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+' on '+str(date_taken)+'</span> ]</center><br>' +
                            '<table class="table">'+

                            '<thead>'+
                                '<tr>'+
                                '<th scope="col">Fieldwork Location</th>'+
                                '</tr>'+
                            '</thead>'+

                            '<tbody>'+
                                '<tr>'+
                                '<th><img class="img-thumbnail" src="data:image/png;base64,'+str(image)+'" ismap /></th>'
                                '</tr>'+
                            '</tbody>'+

                            '</table>'+

                            '<form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;">'+
                            '<div class="form-group">'+
                            '<input type="hidden" value="'+str(imginv)+'" name="imginv">'+
                            '<input type="hidden" value="'+str(loninv)+'" name="loninv">'+
                            '<input type="hidden" value="'+str(latinv)+'" name="latinv">'+
                            '<input type="hidden" value="'+str(altinv)+'" name="altinv">'+
                            '<input type="hidden" value="'+str(date_taken)+'" name="date">'+
                            '<input type="hidden" value="'+image+'" name="imag">'+
                            '<input type="hidden" value="'+str(takeoff)+'" name="takeoff">'+
                            '<input type="hidden" value="'+str(landing)+'" name="landing">'+
                            '<input type="hidden" value="'+str(role)+'" name="role">'+
                            '<input type="hidden" value="'+str(antypelist)+'" name="antypelist">'+
                            '<input type="hidden" value="'+str(flight_id)+'" name="flightid">'+
                            '<input type="hidden" value="'+str(longitude)+'" name="lonnormal">'+
                            '<input type="hidden" value="'+str(latitude)+'" name="latnormal">'+
                            '<input class="form-control"  type="submit" value="More Info"> </form>'+
                            '</div>')
            objectname = 'object'+str(x)
            marker.update({objectname:{'lat':latitude, 'lng':longitude, 'description':description}})
            #marker.update({objectname:{'lat':latitude, 'lng':longitude}})


            x+=1
            
        center_lat = lat[-1]
        center_lon = lon[-1]
        center_position = str(center_lon)+','+str(center_lat)
        dates = list(sorted(set(dates)))
        dates2 = list(sorted(set(dates2)))

        #end
        print("marker {}".format(marker.keys()))
        print("len marker {}".format(len(marker)))
        user_request[username]={'data':json.dumps(marker),'sent':False}
        return ('', 204)
    else:
        return redirect(url_for('login'))

@app.route('/streamadmin')
@flask_login.login_required
def streamadmin():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        global user_request
        #print ("Test user_request : {}".format(user_request))
        if not username in user_request:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        elif not user_request[username]['sent']:
            response = app.response_class(
            response="data:%s\n\n"% user_request[username]['data'],
            status=200,
            mimetype='text/event-stream'
            )
            user_request[username]['sent']=True
        elif user_request[username]['sent']:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        return response
    else:
        return redirect(url_for('login'))

@app.route('/push', methods=['GET'])
@flask_login.login_required
def push():
    datel = []
    if flask_login.current_user.is_authenticated:
        date = request.args.get('date')
        date = str(date)
        username = flask_login.current_user.id

        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        userentry = cursor.fetchone()

        username=userentry['username']

        datel.append(date)
        global user_request


    #start
    print("this is date {}".format(date))
    cursor.execute('SELECT * FROM flight WHERE username=? AND date_taken LIKE ?', (username,date+"%",))
    entry = cursor.fetchall()

    if entry:
        print("YES MATCH!")
        x=1
        marker={}
        lat = []
        lon = []
        dates = []
        dates2 = []
        img=[]
        total_row=len(entry)
        timetakeoff =[]
        timelanding = []

        for row in entry:
            print("enter here 2nd row")
            print("date matching : {}".format(row['date_taken']))
            imginv = []
            latinv = []
            loninv = []
            antypelist = []
            altinv = []
            
            flight_id = row['flight_id']
            print(flight_id)
            altitude = row['altitude']
            latitude = row['latitude']
            longitude = row['longitude']
            date_taken = row['date_taken']
            user= row['username']
            image = row['loc_image']
            takeoff = row['takeoff']
            landing = row['landing']
            role = 0
            takeoff = (datetime.strptime(takeoff,'%H:%M:%S').time())
            landing = (datetime.strptime(landing,'%H:%M:%S').time())

            img.append(image)
            lat.append(float(row['latitude']))
            lon.append(float(row['longitude']))
            dates.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))
            dates2.append(str(datetime.strptime(date_taken, '%Y-%m-%d %H:%M:%S').strftime('X%d-X%m-%Y').replace('X0','X').replace('X','')))

            cursor.execute('SELECT * FROM data_table WHERE flight_id=?', (flight_id,))
            entry2 = cursor.fetchall()
            
            for i in entry2:
                print("enter 3rd row")
                
                #append data inv table
                image2 = i['image']
                lati = i['latitude']
                user2= i['username']
                loni = i['longitude']
                antype = i['type']
                alt = i['altitude']

                antenna = changeAntenna(antype) #change antenna name

                latinv.append(lati)
                loninv.append(loni)
                imginv.append(image2)
                antypelist.append(antenna)
                altinv.append(alt)

            print("all altitude : {}".format(altinv))

            #description = '<b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+'</span> ]</b><br><br><b>Lon/Lat : </b>'+str(longitude)+'&#176 , '+str(latitude)+'&#176'+'<br><b>Date/Time : </b>'+str(date_taken)+'<br><br><center><b>Fieldwork View </b><br><br>'+'<img style="height: 60%; width: 60%;" src="data:image/png;base64,'+str(image)+'" ismap /></center><br><form action="/showinv" accept-charset="UTF-8" method="post" target="_blank" style="text-align: center; margin:3px;"><input type="hidden" value="'+str(imginv)+'" name="imginv"><input type="hidden" value="'+str(loninv)+'" name="loninv"> <input type="hidden" value="'+str(latinv)+'" name="latinv"> <input type="hidden" value="'+str(altinv)+'" name="altinv"> <input type="hidden" value="'+str(date_taken)+'" name="date"><input type="hidden" value="'+image+'" name="imag"> <input type="hidden" value="'+str(takeoff)+'" name="takeoff"><input type="hidden" value="'+str(landing)+'" name="landing"><input type="hidden" value="'+str(role)+'" name="role"> <input type="hidden" value="'+str(antypelist)+'" name="antypelist"> <input type="hidden" value="'+str(flight_id)+'" name="flightid"> <input style="width:50%;" type="submit" value="More Info"> </form>'
            #description = 'kentang'
            description = ( '<center><b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+' on '+str(date_taken)+'</span> ]</center><br>' +
                            '<table class="table">'+

                            '<thead>'+
                                '<tr>'+
                                '<th scope="col">Fieldwork Location</th>'+
                                '</tr>'+
                            '</thead>'+

                            '<tbody>'+
                                '<tr>'+
                                '<th><img class="img-thumbnail" src="data:image/png;base64,'+str(image)+'" ismap /></th>'
                                '</tr>'+
                            '</tbody>'+

                            '</table>'+

                            '<form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;">'+
                            '<div class="form-group">'+
                            '<input type="hidden" value="'+str(imginv)+'" name="imginv">'+
                            '<input type="hidden" value="'+str(loninv)+'" name="loninv">'+
                            '<input type="hidden" value="'+str(latinv)+'" name="latinv">'+
                            '<input type="hidden" value="'+str(altinv)+'" name="altinv">'+
                            '<input type="hidden" value="'+str(date_taken)+'" name="date">'+
                            '<input type="hidden" value="'+image+'" name="imag">'+
                            '<input type="hidden" value="'+str(takeoff)+'" name="takeoff">'+
                            '<input type="hidden" value="'+str(landing)+'" name="landing">'+
                            '<input type="hidden" value="'+str(role)+'" name="role">'+
                            '<input type="hidden" value="'+str(antypelist)+'" name="antypelist">'+
                            '<input type="hidden" value="'+str(flight_id)+'" name="flightid">'+
                            '<input type="hidden" value="'+str(longitude)+'" name="lonnormal">'+
                            '<input type="hidden" value="'+str(latitude)+'" name="latnormal">'+
                            '<input class="form-control"  type="submit" value="More Info"> </form>'+
                            '</div>')
            objectname = 'object'+str(x)
            marker.update({objectname:{'lat':latitude, 'lng':longitude, 'description':description}})


            x+=1
            
        center_lat = lat[-1]
        center_lon = lon[-1]
        center_position = str(center_lon)+','+str(center_lat)
        dates = list(sorted(set(dates)))
        dates2 = list(sorted(set(dates2)))

        #end
        print("len marker {}".format(len(marker)))
        user_request[username]={'data':json.dumps(marker),'sent':False}
        return ('', 204)
    else:
        return redirect(url_for('login'))

@app.route('/stream')
@flask_login.login_required
def stream():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id

        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        userentry = cursor.fetchone()

        username=userentry['username']

        global user_request
        #print ("Test user_request : {}".format(user_request))
        if not username in user_request:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        elif not user_request[username]['sent']:
            response = app.response_class(
            response="data:%s\n\n"% user_request[username]['data'],
            status=200,
            mimetype='text/event-stream'
            )
            user_request[username]['sent']=True
        elif user_request[username]['sent']:
            response = app.response_class(
            response="data:no data\n\n",
            status=200,
            mimetype='text/event-stream'
            )
        return response
    else:
        return redirect(url_for('login'))


@app.route('/userdash')
@flask_login.login_required
def userdash():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()

        cursor.execute('SELECT * FROM user_table WHERE privilage = 7 ')
        lenadmin = cursor.fetchall()

        cursor.execute('SELECT * FROM user_table WHERE privilage = 0 ')
        lenuser = cursor.fetchall()

        

        if entry :
            if entry['privilage']==0:
                return render_template('dash/dashboard.html', lenadmin=lenadmin, lenuser=lenuser) #user dashboard
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


def findCenterLonLat (geolocations): # ( (12,23),(23,23),(43,45) )
    x,y,z =0,0,0
    #print(geolocations)

    for lat, lon in (geolocations):
        #print('\n\n')
        #print(lat)
        #print(lon)
        #print('\n\n')
        lat = math.radians(float(lat))
        lon = math.radians(float(lon))
        x += math.cos(lat) * math.cos(lon)
        y += math.cos(lat) * math.sin(lon)
        z += math.sin(lat)

    x = float(x / len(geolocations))
    y = float(y / len(geolocations))
    z = float(z / len(geolocations)) 
    
    center_lon = (math.atan2(y, x))
    center_lat = math.atan2(z, math.sqrt(x * x + y * y))

    return (math.degrees(center_lat), math.degrees(center_lon))
    
global min1, min2, max1, max2, dname
min1,min2,max1,max2=0,0,0,0
dname = "View All State"

@app.route('/adminmap')
@flask_login.login_required
def adminmap():
    error=None
    username=flask_login.current_user.id
    print ("adminmap = {}".format(username))
     

    min1 = request.args.get("min1") #minlat
    min2 = request.args.get("min2") #minlon
    max1 = request.args.get("max1") #maxlat
    max2 = request.args.get("max2") #maxlon
    dname = request.args.get("dname")

    telco=None
    entry2 = None

    if (min1 is None):
        min1, min2, max1, max2 = 0,0,0,0
    else :
        min1, min2, max1, max2 = min1, min2, max1, max2 
       
        #print("min lat: "+str(min1))
        #print("max lat: "+str(min2))
        #print("min lon: "+str(max1))
        #print("max lon: "+str(max2))

        #print("1-- {}, 2-- {}, 3-- {}, 4-- {}".format(min1,min2,max1,max2))
        try:
            lock.acquire(True)
            cursor.execute('SELECT * FROM telco WHERE lat>? AND lat<? AND lon>? AND lon<? AND samples>? AND created = updated', (min1, min2, max1, max2, "10",))
            entry2 = cursor.fetchall()
        finally:
            lock.release()
        
        tot = len(entry2)

    if entry2 != None:

        tower_ids = set()
        for areaid in entry2:
            tower_ids.add(areaid['area'])

        flash('Focus on {} with {} tower(s) and {} antenna(s)'.format(dname, len(tower_ids), tot))
        error = str("Focus on {} with {} tower(s) {} antenna(s)".format(dname,len(tower_ids), tot))

        telco = {}
        y=1

        for id in tower_ids:
            try:
                lock.acquire(True)
                cursor.execute('SELECT * FROM telco WHERE area =? AND lat>? AND lat<? AND lon>? AND lon<? AND samples>?', (id, min1, min2, max1, max2, "10",))
                entry5 = cursor.fetchall()
                lenentry = len(entry5)
            finally:
                lock.release()
            
            

            latlon_list = [ (x['lat'], x['lon']) for x in entry5]
            netlist = []

            for x in entry5:
                tnet = x['net']
                mcc = x['mcc']
                radio = x['radio']
                rangee = x['range']

                if tnet == "01":
                    tnet="Art900"
                elif tnet == "10":
                    tnet="Digi Telecommuncations"
                elif tnet == "11":
                    tnet="MTX Utara"
                elif tnet == "12":
                    tnet="Maxis"
                elif tnet == "13":
                    tnet="Celcom"
                elif tnet == "151":
                    tnet="Baraka Telecom Sdn Bhd"
                elif tnet == "152":
                    tnet="YES"
                elif tnet == "153":
                    tnet="Webe/Packet One Networks (Malaysia) Sdn Bhd"
                elif tnet == "154":
                    tnet="Tron/Talk Focus Sdn Bhd"
                elif tnet == "155":
                    tnet="Samata Communications Sdn Bhd"
                elif tnet == "16":
                    tnet="Digi Telecommunications"
                elif tnet == "17":
                    tnet="Maxis"
                elif tnet == "18":
                    tnet="U Mobile"
                elif tnet == "19":
                    tnet="Celcom"
                elif tnet == "195":
                    tnet="XOX Com Sdn Bhd"
                elif tnet == "198":
                    tnet="Celcom"
                elif tnet == "20":
                    tnet="Electcoms Wireless Sdn Bhd"
                else: tnet="--"

                netlist.append(tnet)
            
            

            lat,lon = findCenterLonLat(latlon_list)

            latlist, lonlist = [],[]
            netlist = list(set(netlist))
            netlist=x = ", ".join(netlist)

            latlist.append(lat)
            lonlist.append(lon)

            description2 = ('<b>MCC</b>: '+str(mcc)+
                            '<br><b>Network</b>: '+str(tnet)+
                            '<br><b>Radio Type</b>: '+str(radio)+
                            '<br><br><b>Latitude</b>: '+str(lat)+
                            '<br><b>Longitude</b>: '+str(lon)+
                            '<br><b>Range</b>: '+str(rangee))


           
            #description2 = ('<h4> Tower Info </h4><br>'+
            #                '<p>Latlon :<span style="color:blue"> {} , {}</span></p><p>Area: <span style="color:blue">{}</span></p> <p>Network : <span style="color:blue"> {} </span></p> <p>No of Antenna:<span style="color:blue"> {}</span></p> '.format(round(lat, 3),round(lon, 2),str(id),str(netlist),str(lenentry)))
            objecttelco = 'object'+str(y)
            telco.update({objecttelco:{'lat':lat, 'lng':lon,'description':description2}})
            y+=1

            #print("Total Info -> Area {} <- ({})".format(id,len(entry5)))
    
    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()
    finally:
        lock.release()
    
    if entry['privilage']==7:
        #print("yes enter!!")
        x=1
        marker={}
        lat = []
        lon = []
        datenew = []
        time = []
        timetakeoff = []
        timelanding = []
        userss = []
        img = []                        
        img33 = []

        listdate = []
        listusername = []
        try:
            lock.acquire(True)
            cursor.execute('SELECT date_taken, username FROM flight')
            entry3 = cursor.fetchall()
        finally:
            lock.release()
        

        for i in entry3:
            date_taken = i['date_taken']
            username = i['username']
            listdate.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))
            listusername.append(str(username))

        try:
            lock.acquire(True)
            cursor.execute('SELECT *,MAX(date_taken) FROM flight')
            entry1 = cursor.fetchall()
        finally:
            lock.release()

        

        for row in entry1:
            imginv = []
            latinv = []
            loninv = []
            antypelist = []
            altinv = []
            flight_id = row['flight_id']

            altitude = row['altitude']
            latitude = row['latitude']
            longitude = row['longitude']
            date_taken = row['date_taken']
            takeoff = row['takeoff']
            landing = row['landing']
            user= row['username']
            image = row['loc_image']
            roundlat = round(float(latitude),3)
            roundlon = round(float(longitude),3)
            role = 1

            #append flight table
            img.append(image)
            lat.append(float(row['latitude']))
            lon.append(float(row['longitude']))
            
            datenew.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))
            time.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').time()))

            timetakeoff.append(str(datetime.strptime(takeoff,'%H:%M:%S').time()))
            timelanding.append(str(datetime.strptime(landing,'%H:%M:%S').time()))

            takeoff = (datetime.strptime(takeoff,'%H:%M:%S').time())
            landing = (datetime.strptime(landing,'%H:%M:%S').time())

            userss.append(user)

            try:
                lock.acquire(True)
                cursor.execute('SELECT * FROM data_table WHERE flight_id=?', (flight_id,))
                entry2 = cursor.fetchall()
            finally:
                lock.release()
            
            for i in entry2:
                print("enter 3rd row")
                
                #append data inv table
                image2 = i['image']
                lati = i['latitude']
                user2= i['username']
                loni = i['longitude']
                antype = i['type']
                alt = i['altitude']

                antenna = changeAntenna(antype) #change antenna name

                latinv.append(lati)
                loninv.append(loni)
                imginv.append(image2)
                antypelist.append(antenna)
                altinv.append(alt)

            print("all altitude : {}".format(altinv))
            lonnormal = longitude
            latnormal = latitude
            print("Lat {}, Lon {}".format(latnormal, lonnormal))
            print("TYPE Lat {}, Lon {}".format(type(latnormal), type(lonnormal)))
            '''
            description = ('<b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+'</span> ]' +
                            '</b><br><br><b>Lon/Lat : </b>'+str(longitude)+'&#176 , '+str(latitude)+'&#176'+
                            '<br><b>Date/Time : </b>'+str(date_taken)+
                            '<br><br><center><b>Fieldwork View </b><br><br>'+
                            '<img style="height: 60%; width: 60%;" src="data:image/png;base64,'+str(image)+'" ismap /></center><br>'+
                            
                            '<form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;">'+
                            '<input type="hidden" value="'+str(imginv)+'" name="imginv"><input type="hidden" value="'+str(loninv)+'" name="loninv"> <input type="hidden" value="'+str(latinv)+'" name="latinv"> <input type="hidden" value="'+str(altinv)+'" name="altinv"> <input type="hidden" value="'+str(date_taken)+'" name="date"><input type="hidden" value="'+image+'" name="imag"> <input type="hidden" value="'+str(takeoff)+'" name="takeoff"><input type="hidden" value="'+str(landing)+'" name="landing"><input type="hidden" value="'+str(role)+'" name="role"> <input type="hidden" value="'+str(antypelist)+'" name="antypelist"> <input type="hidden" value="'+str(flight_id)+'" name="flightid"> <input style="width:50%;" type="submit" value="More Info"> </form>')
            '''
            description = ( '<center><b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+' on '+str(date_taken)+'</span> ]</center><br>' +
                            '<table class="table">'+

                            '<thead>'+
                                '<tr>'+
                                '<th scope="col">Fieldwork Location</th>'+
                                '</tr>'+
                            '</thead>'+

                            '<tbody>'+
                                '<tr>'+
                                '<th><img class="img-thumbnail" src="data:image/png;base64,'+str(image)+'" ismap /></th>'
                                '</tr>'+
                            '</tbody>'+

                            '</table>'+

                            '<form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;">'+
                            '<div class="form-group">'+
                            '<input type="hidden" value="'+str(imginv)+'" name="imginv">'+
                            '<input type="hidden" value="'+str(loninv)+'" name="loninv">'+
                            '<input type="hidden" value="'+str(latinv)+'" name="latinv">'+
                            '<input type="hidden" value="'+str(altinv)+'" name="altinv">'+
                            '<input type="hidden" value="'+str(date_taken)+'" name="date">'+
                            '<input type="hidden" value="'+image+'" name="imag">'+
                            '<input type="hidden" value="'+str(takeoff)+'" name="takeoff">'+
                            '<input type="hidden" value="'+str(landing)+'" name="landing">'+
                            '<input type="hidden" value="'+str(role)+'" name="role">'+
                            '<input type="hidden" value="'+str(antypelist)+'" name="antypelist">'+
                            '<input type="hidden" value="'+str(flight_id)+'" name="flightid">'+
                            '<input type="hidden" value="'+str(longitude)+'" name="lonnormal">'+
                            '<input type="hidden" value="'+str(latitude)+'" name="latnormal">'+
                            '<input class="form-control"  type="submit" value="More Info"> </form>'+
                            '</div>')

            objectname = 'object'+str(x)
            marker.update({objectname:{'lat':latitude, 'lng':longitude, 'description':description}})
            

            x+=1

        #print(datenew)
        #print("gaggagagagga==============================")
        #print(img)
        center_lat = lat[-1]
        center_lon = lon[-1]
        center_position = str(center_lon)+','+str(center_lat)
        #print("latest position {}".format(center_position))
        #print(user)
        dates = list(sorted(set(datenew)))
        listdate = list(sorted(set(listdate)))
        user = list(set(userss))
        listusername = list(set(listusername))
        #print(user)
        print("Total data send to HTML: {}".format(len(marker)))
        print(center_lat)


    return render_template('/dash/admin-maps3.html', altitude=altitude, clat = center_lat, clon = center_lon, error=error, telco=telco, image=image, img=img, date_taken=date_taken, dname=dname, min1=min1, min2=min2, max1=max1, max2=max2, data=json.dumps(listdate), marker=marker, center=center_position, username=username, user=listusername, dates=dates)



@app.route('/usermap')
@flask_login.login_required
def usermap():
    username=flask_login.current_user.id 

    cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
    userentry = cursor.fetchone()

    username=userentry['username']

    min1 = request.args.get("min1") #minlat
    min2 = request.args.get("min2") #minlon
    max1 = request.args.get("max1") #maxlat
    max2 = request.args.get("max2") #maxlon
    dname = request.args.get("dname")
    telco=None

    entry2 = None


    if (min1 is None):
        min1, min2, max1, max2 = 0,0,0,0
    else :
        min1, min2, max1, max2 = min1, min2, max1, max2
        
        print("min lat: "+str(min1))
        print("max lat: "+str(min2))
        print("min lon: "+str(max1))
        print("max lon: "+str(max2))
        
        try:
            lock.acquire(True)
            cursor.execute('SELECT * FROM telco WHERE lat>? AND lat<? AND lon>? AND lon<? AND samples>? AND created = updated', (min1, min2, max1, max2, "10",))
            entry2 = cursor.fetchall()
            tot = len(entry2)
        finally:
            lock.release()
        

    if entry2 != None:

        tower_ids = set()
        for areaid in entry2:
            tower_ids.add(areaid['area'])

        flash('Focus on {} with {} tower(s) and {} antenna(s)'.format(dname, len(tower_ids), tot))
        error = str("Focus on {} with {} tower(s) {} antenna(s)".format(dname,len(tower_ids), tot))

        telco = {}
        y=1

        for id in tower_ids:
            

            try:
                lock.acquire(True)
                cursor.execute('SELECT * FROM telco WHERE area =? AND lat>? AND lat<? AND lon>? AND lon<? AND samples>?', (id, min1, min2, max1, max2, "10",))
                entry5 = cursor.fetchall()
            finally:
                lock.release()

            lenentry = len(entry5)

            latlon_list = [ (x['lat'], x['lon']) for x in entry5]
            netlist = []

            for x in entry5:
                tnet = x['net']
                mcc = x['mcc']
                radio = x['radio']
                rangee = x['range']

                if tnet == "01":
                    tnet="Art900"
                elif tnet == "10":
                    tnet="Digi Telecommuncations"
                elif tnet == "11":
                    tnet="MTX Utara"
                elif tnet == "12":
                    tnet="Maxis"
                elif tnet == "13":
                    tnet="Celcom"
                elif tnet == "151":
                    tnet="Baraka Telecom Sdn Bhd"
                elif tnet == "152":
                    tnet="YES"
                elif tnet == "153":
                    tnet="Webe/Packet One Networks (Malaysia) Sdn Bhd"
                elif tnet == "154":
                    tnet="Tron/Talk Focus Sdn Bhd"
                elif tnet == "155":
                    tnet="Samata Communications Sdn Bhd"
                elif tnet == "16":
                    tnet="Digi Telecommunications"
                elif tnet == "17":
                    tnet="Maxis"
                elif tnet == "18":
                    tnet="U Mobile"
                elif tnet == "19":
                    tnet="Celcom"
                elif tnet == "195":
                    tnet="XOX Com Sdn Bhd"
                elif tnet == "198":
                    tnet="Celcom"
                elif tnet == "20":
                    tnet="Electcoms Wireless Sdn Bhd"
                else: tnet="--"

                netlist.append(tnet)
            
            

            lat,lon = findCenterLonLat(latlon_list)

            latlist, lonlist = [],[]
            netlist = list(set(netlist))
            netlist=x = ", ".join(netlist)

            latlist.append(lat)
            lonlist.append(lon)

            #description2 = '<h4>Tower Info</h4><br><span>LonLat :'+str(lat)+','+str(lon)+"</span>"

            description2 = ('<b>MCC</b>: '+str(mcc)+
                            '<br><b>Network</b>: '+str(tnet)+
                            '<br><b>Radio Type</b>: '+str(radio)+
                            '<br><br><b>Latitude</b>: '+str(lat)+
                            '<br><b>Longitude</b>: '+str(lon)+
                            '<br><b>Range</b>: '+str(rangee))

            objecttelco = 'object'+str(y)
            telco.update({objecttelco:{'lat':lat, 'lng':lon,'description':description2}})
            y+=1

            #print("Total Info -> Area {} <- ({})".format(id,len(entry5)))


    listdate = []

    try:
        lock.acquire(True)
        cursor.execute('SELECT date_taken FROM flight WHERE username=? ', (username,))
        entry3 = cursor.fetchall()
    finally:
        lock.release()
    

    for i in entry3:
        date_taken = i['date_taken']
        listdate.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))

    try:
        lock.acquire(True)
        cursor.execute('SELECT *, MAX(date_taken) FROM flight WHERE username=? ', (username,))
        entry = cursor.fetchall()
    finally:
        lock.release()
    
    print("list number entry : {}".format(len(entry)))

    if entry:
        x=1
        marker={}
        lat = []
        lon = []
        dates = []
        dates2 = []
        img=[]
        total_row=len(entry)
        timetakeoff =[]
        timelanding = []

        for row in entry:
            imginv = []
            latinv = []
            loninv = []
            antypelist = []
            altinv = []
            
            flight_id = row['flight_id']
            altitude = row['altitude']
            latitude = row['latitude']
            longitude = row['longitude']
            date_taken = row['date_taken']
            user= row['username']
            image = row['loc_image']
            takeoff = row['takeoff']
            landing = row['landing']
            role = 0
            takeoff = (datetime.strptime(takeoff,'%H:%M:%S').time())
            landing = (datetime.strptime(landing,'%H:%M:%S').time())

            img.append(image)
            lat.append(float(row['latitude']))
            lon.append(float(row['longitude']))
            dates.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))
            dates2.append(str(datetime.strptime(date_taken, '%Y-%m-%d %H:%M:%S').strftime('X%d-X%m-%Y').replace('X0','X').replace('X','')))
            
            try:
                lock.acquire(True)
                cursor.execute('SELECT * FROM data_table WHERE flight_id=?', (flight_id,))
                entry2 = cursor.fetchall()
            finally:
                lock.release()
            
            
            for i in entry2:
                print("enter 3rd row")
                
                #append data inv table
                image2 = i['image']
                lati = i['latitude']
                user2= i['username']
                loni = i['longitude']
                antype = i['type']
                alt = i['altitude']

                print(alt)

                antenna = changeAntenna(antype) #change antenna name

                latinv.append(lati)
                loninv.append(loni)
                imginv.append(image2)
                antypelist.append(antenna)
                altinv.append(alt)

            print("all altitude : {}".format(altinv))
            sys.stdout.flush()

            #description = '<b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+'</span> ]</b><br><br><b>Lon/Lat : </b>'+str(longitude)+'&#176 , '+str(latitude)+'&#176'+'<br><b>Date/Time : </b>'+str(date_taken)+'<br><br><center><b>Fieldwork View </b><br><br>'+'<img style="height: 60%; width: 60%;" src="data:image/png;base64,'+str(image)+'" ismap /></center><br><form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;"><input type="hidden" value="'+str(imginv)+'" name="imginv"><input type="hidden" value="'+str(loninv)+'" name="loninv"> <input type="hidden" value="'+str(latinv)+'" name="latinv"> <input type="hidden" value="'+str(altinv)+'" name="altinv"> <input type="hidden" value="'+str(date_taken)+'" name="date"><input type="hidden" value="'+image+'" name="imag"> <input type="hidden" value="'+str(takeoff)+'" name="takeoff"><input type="hidden" value="'+str(landing)+'" name="landing"><input type="hidden" value="'+str(role)+'" name="role"> <input type="hidden" value="'+str(antypelist)+'" name="antypelist"> <input type="hidden" value="'+str(flight_id)+'" name="flightid"> <input style="width:50%;" type="submit" value="More Info"> </form>'
            #description = 'kentang'
            description = ( '<center><b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+' on '+str(date_taken)+'</span> ]</center><br>' +
                            '<table class="table">'+

                            '<thead>'+
                                '<tr>'+
                                '<th scope="col">Fieldwork Location</th>'+
                                '</tr>'+
                            '</thead>'+

                            '<tbody>'+
                                '<tr>'+
                                '<th><img class="img-thumbnail" src="data:image/png;base64,'+str(image)+'" ismap /></th>'
                                '</tr>'+
                            '</tbody>'+

                            '</table>'+

                            '<form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;">'+
                            '<div class="form-group">'+
                            '<input type="hidden" value="'+str(imginv)+'" name="imginv">'+
                            '<input type="hidden" value="'+str(loninv)+'" name="loninv">'+
                            '<input type="hidden" value="'+str(latinv)+'" name="latinv">'+
                            '<input type="hidden" value="'+str(altinv)+'" name="altinv">'+
                            '<input type="hidden" value="'+str(date_taken)+'" name="date">'+
                            '<input type="hidden" value="'+image+'" name="imag">'+
                            '<input type="hidden" value="'+str(takeoff)+'" name="takeoff">'+
                            '<input type="hidden" value="'+str(landing)+'" name="landing">'+
                            '<input type="hidden" value="'+str(role)+'" name="role">'+
                            '<input type="hidden" value="'+str(antypelist)+'" name="antypelist">'+
                            '<input type="hidden" value="'+str(flight_id)+'" name="flightid">'+
                            '<input type="hidden" value="'+str(longitude)+'" name="lonnormal">'+
                            '<input type="hidden" value="'+str(latitude)+'" name="latnormal">'+
                            '<input class="form-control"  type="submit" value="More Info"> </form>'+
                            '</div>')
            objectname = 'object'+str(x)
            marker.update({objectname:{'lat':latitude, 'lng':longitude, 'description':description}})

            x+=1
            
        center_lat = lat[-1]
        center_lon = lon[-1]
        center_position = str(center_lon)+','+str(center_lat)
        dates = list(sorted(set(dates)))
        dates2 = list(sorted(set(dates2)))
        listdate = list(sorted(set(listdate)))
        print(listdate)

        return render_template('/dash/user-map3.html',telco=telco, clat = center_lat, clon = center_lon, dname=dname,min1=min1, img=img, min2=min2, max1=max1, max2=max2, marker=marker,  center=center_position, username=username, dates=dates, data=json.dumps(listdate))

    else :
        return ("error")

'''
@app.route('/searchlocadmin',methods=['POST'])
@flask_login.login_required
def searchlocadmin():
    username=flask_login.current_user.id
    
    if flask_login.current_user.is_authenticated:
        loc = request.form.get('state')
    
    if (' ' in loc) :
        splitted    = loc.split()
        first       = splitted[0]
        second      = splitted[1]
        locnew      = ("{}%20{}".format(first,second))
    else :
        locnew = loc

    url = "https://nominatim.openstreetmap.org/search/"+locnew+"?format=json&addressdetails=1&limit=2"
    print(url)

    data = requests.get(url=url).text
    data = json.loads(data)

    for i in data:
        bounding = ('{},{},{},{}'.format(i['boundingbox'][0],i['boundingbox'][1],i['boundingbox'][2],i['boundingbox'][3]))
        minlat    = ('{}'.format(i['boundingbox'][0]))
        minlon    = ('{}'.format(i['boundingbox'][1]))
        maxlat    = ('{}'.format(i['boundingbox'][2]))
        maxlon    = ('{}'.format(i['boundingbox'][3]))

        #minlat, minlon, maxlat, maxlon = "2.876833", "2.982444", "101.659687", "101.732682"
        
        dname = ('{}'.format(i['display_name']))
    
    print("{} / {} / {} / {}".format(minlat,minlon,maxlat,maxlon))


    return redirect(url_for('adminmap', min1=minlat, min2=minlon, max1=maxlat, max2=maxlon, dname=dname))
'''


@app.route('/searchloc',methods=['POST'])
@flask_login.login_required
def searchloc():
    username=flask_login.current_user.id
    
    if flask_login.current_user.is_authenticated:
        loc = request.form.get('state')
    
    if (' ' in loc) :
        splitted    = loc.split()
        first       = splitted[0]
        second      = splitted[1]
        locnew      = ("{}%20{}".format(first,second))
    else :
        locnew = loc

    url = "https://nominatim.openstreetmap.org/search/"+locnew+"?format=json&addressdetails=1&limit=1"
    print(url)

    data = requests.get(url=url).text
    data = json.loads(data)
    
    if ('putrajaya' in loc) :
        minlat, minlon, maxlat, maxlon = "2.876833", "2.982444", "101.659687", "101.732682"
        dname = ('{}'.format("Putrajaya"))
    
    else:
        for i in data:
            #bounding = ('{},{},{},{}'.format(i['boundingbox'][0],i['boundingbox'][1],i['boundingbox'][2],i['boundingbox'][3]))
            minlat    = ('{}'.format(i['boundingbox'][0]))
            minlon    = ('{}'.format(i['boundingbox'][1]))
            maxlat    = ('{}'.format(i['boundingbox'][2]))
            maxlon    = ('{}'.format(i['boundingbox'][3]))

            #minlat, minlon, maxlat, maxlon = "2.876833", "2.982444", "101.659687", "101.732682"
            
            dname = ('{}'.format(i['display_name']))
    
    cursor.execute('SELECT privilage FROM user_table WHERE status_log=?', (username,))
    entry = cursor.fetchone()

    if entry['privilage']==7:
        return redirect(url_for('adminmap', min1=minlat, min2=minlon, max1=maxlat, max2=maxlon, dname=dname))
    elif entry['privilage']==0:
        return redirect(url_for('usermap', min1=minlat, min2=minlon, max1=maxlat, max2=maxlon, dname=dname))
    else :
        return "Error!"


@app.route('/showinv', methods=['POST'])
@flask_login.login_required
def showinv():
    username=flask_login.current_user.id
    splitinv = []
    newlat = []
    newlon = []
    newtype = []
    newalt = []

    simage = request.form.get('imag') #form
    date = request.form.get('date') #form
    inv = request.form.get('imginv') #form
    lon = request.form.get('loninv') #form
    lat = request.form.get('latinv') #form
    role = request.form.get('role') #form
    user = request.form.get('username') #form
    landing = request.form.get('landing') #form
    takeoff = request.form.get('takeoff') #form
    flight_id = request.form.get('flightid')
    antypelist = request.form.get('antypelist')
    lonnormal = request.form.get('lonnormal')
    latnormal = request.form.get('latnormal')
    alt = request.form.get('altinv')
    latlon = ("{},{}".format(latnormal,lonnormal))
    #print("image: {}".format(inv))
    FMT = '%H:%M:%S'
    tdelta = datetime.strptime(landing, FMT) - datetime.strptime(takeoff, FMT)


    #print("duration : {}".format(str(tdelta)))

    #print("hasil lat : {}".format(str(lat)))
    #print("hasil lon : {}".format(str(lon)))

    #print("hasil image : {}".format(str(inv)))

    splitinv = remove_dirty_form(inv)

    newlat = remove_dirty_form(lat)

    newlon = remove_dirty_form(lon)

    newalt = remove_dirty_form(alt,number=True)

    newtype = remove_dirty_form(antypelist)



    #print("list image : {}".format(splitinv))

    lonnormal = round(float(lonnormal),4)
    latnormal = round(float(latnormal),4)

    print("normal lat {}, normal lon {}".format(latnormal, lonnormal))
    print("type normal lat {}, normal lon {}".format(type(latnormal), type(lonnormal)))
    

    #print(splitinv)
    print(type(splitinv))

    return render_template('/dash/showinv2.html', list_inv=zip(newalt, newlat, newlon, splitinv,newtype), lonnormal=lonnormal, latnormal=latnormal,  username=username, flight_id=flight_id, landing=landing, takeoff=takeoff, tdelta=tdelta)


@app.route('/map')
@flask_login.login_required
def show_map():
    username=flask_login.current_user.id
    #print(username)
    cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
    userentry = cursor.fetchone()
    #print(entry)
    username=userentry['username']

    cursor.execute('SELECT * FROM data_table WHERE username=? ', (username,))
    entry = cursor.fetchall()


    if entry is None:
        flask_login.logout_user()
        return redirect(url_for('login'))
    elif not entry:
        flask_login.logout_user()
        return render_template('empty_map.html')
    else :
        print("got it")
        return redirect(url_for('userdash'))

@app.route('/admin')
@flask_login.login_required
def show_admin():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        print ("show_admin = {}".format(username))
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                return render_template('dash/adminboard.html')
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/update_admin')
@flask_login.login_required
def update_admin():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()

        if entry :
            if entry['privilage']==7:
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
                return render_template('dash/table.html', users=entry)
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/userlist')
@flask_login.login_required
def show_userlist():
    
    user=[]
    passs=[]

    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        print ("show_userlist = {}".format(username))
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry= cursor.fetchone()
        #print (entry)

        username=entry['username']

        if entry :
            if entry['privilage']==7:
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
               
                return render_template('dash/table.html', users=entry, username=username)
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/userprofile')
@flask_login.login_required
def show_userprofile():


    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        print ("show_userprofile = {}".format(username))
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()

        password=entry['password']
        username=entry['username']
        privilage=entry['privilage']
        date_created=entry['date_created']

        if privilage == 7:
            privilagelabel = "Admin"
        else:
            privilagelabel = "User"

        if entry :
            if entry['privilage']==7:
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
                return render_template('dash/user.html', users=entry, username=username, password=password, privilagel=privilagelabel, privilage=privilage, date_created=date_created)
                #flask_login.logout_user()
            
            else :
                cursor.execute('SELECT * FROM user_table')
                entry = cursor.fetchall()
                return render_template('dash/userprof.html', users=entry, username=username, password=password, privilagel=privilagelabel, privilage=privilage, date_created=date_created)
            flask_login.logout_user()
    else:
        return redirect(url_for('login'))

@app.route('/latestID', methods=['GET'])
def latestID():
    cursor.execute('SELECT *,MAX(flight_id) FROM flight')
    entry1 = cursor.fetchone()

    cursor.execute('SELECT *,MAX(id) FROM data_table')
    entry = cursor.fetchone()
    
    datamax = entry['id']
    flightmax = entry1['flight_id']

    return jsonify({'datamax': datamax,'flightmax':flightmax}), 200


@app.route('/insert', methods=['POST'])
def create_record():
    if not request.json or not 'altitude' or not 'latitude' or not 'longitude' or not 'image' or not 'date_taken' or not 'username' or not 'takeoff' or not 'landing' or not 'flight_id' in request.json:
        abort(400)
    
    altitude = request.json['altitude']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    image = request.json['image']
    date_taken = request.json['date_taken']
    username = request.json['username']
    takeoff = request.json['takeoff']
    landing = request.json['landing']
    flight_id = request.json['flight_id']
    print("take off  : {}".format(takeoff))

    cursor.execute('SELECT * FROM flight WHERE (username=? AND takeoff=?)', (username, takeoff,))
    entry = cursor.fetchone()

    if entry is None:
        try:
            cursor.execute('INSERT INTO flight (flight_id,altitude,latitude,longitude,loc_image,date_taken,username,takeoff,landing) VALUES (?,?,?,?,?,?,?,?,?)', (flight_id, altitude, latitude, longitude, image, date_taken, username, takeoff, landing))
            conn.commit()
            return jsonify({'status': 'received'}), 201
        except Exception as e:
            abort(400, e.message+" fail to insert flight id")
    else :
        return jsonify({'status': 'data already recorded'}), 200


@app.route('/insert2', methods=['POST'])
def create_record2():
    if not request.json or not 'altitude' or not 'latitude' or not 'longitude' or not 'image' or not 'date_taken' or not 'username' or not 'type' or not 'id' or not 'flight_id' in request.json:
        abort(400)
    
    altitude = request.json['altitude']
    latitude = request.json['latitude']
    longitude = request.json['longitude']
    image = request.json['image']
    date_taken = request.json['date_taken']
    type = request.json['type']
    flight_id = request.json['flight_id']
    idd = request.json['id']

    username = request.json['username']
    print (flight_id)
    cursor.execute('SELECT * FROM flight WHERE (flight_id=?)', (flight_id,))
    entry = cursor.fetchone()

    if entry:
        try:
            cursor.execute('INSERT INTO data_table (flight_id,id,altitude,latitude,longitude,image,date_taken,username,type) VALUES (?,?,?,?,?,?,?,?,?)', (flight_id, idd, altitude, latitude, longitude, image, date_taken, username,type))
            conn.commit()
            return jsonify({'status': 'received'}), 201
        except Exception as e:
            abort(400, e.message+" fail to insert data")
    else :
        return jsonify({'error': 'no flight id found'}), 400
   
@app.route('/reg', methods=['POST'])
def reg():
    username    = request.form.get('username')
    password    = request.form.get('password')
    #print(username)
    cursor.execute('SELECT * FROM user_table WHERE username=? ', (username,))
    entry = cursor.fetchone()
    #print(entry)

    if entry is None:
        cursor.execute('INSERT INTO user_table (username,password,privilage,enabled,date_created) VALUES (?,?,?,?,?)', (username, password, 0, True, datetime.today().strftime('%Y-%m-%d')))
        conn.commit()
        flash('Welcome {}! You can login now.'.format(username))
        return redirect(url_for('login'))
        
    else:
        flash('Invalid username / Duplicate')
        return redirect(url_for('login'))   

@app.route('/adduser', methods=['POST'])
@flask_login.login_required

def create_user():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id
        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()
        

        if entry :
            if entry['privilage']==7:                
                username    = request.form.get('username')
                password    = request.form.get('password')
                privilage   = request.form.get('privilage')

                if not username or not password or not privilage:
                    abort(400)

                cursor.execute('SELECT * FROM user_table WHERE username=?', (username,))
                entry = cursor.fetchone()

                if entry is None:
                    try:
                        cursor.execute('INSERT INTO user_table (username,password,privilage,enabled,date_created) VALUES (?,?,?,?,?)', (username, password, privilage, True, datetime.today().strftime('%Y-%m-%d')))
                        conn.commit()
                        cursor.execute('SELECT * FROM user_table')
                        entry = cursor.fetchall()
                        flash('You were successfully add new user')
                        return render_template('dash/table.html', users=entry)
                    except Exception as e:
                        print("error")
                else :
                    return jsonify({'status': 'user already recorded'}), 200
                
            flask_login.logout_user()
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/updateuser', methods=['POST'])
@flask_login.login_required
def updateuser():
    if flask_login.current_user.is_authenticated:
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        privilage = request.form.get('privilage')

        if password == repassword:
            cursor.execute('UPDATE user_table SET privilage = ?, password = ? WHERE username = ?', (privilage,password,username))
            flash('You were successfully update user')
            conn.commit()
        else:
            flash('Not saved. Please enter the valid password.')

        

        return redirect(url_for('show_userlist'))

@app.route('/updateuserprof', methods=['POST'])
@flask_login.login_required
def updateuserprof():
    if flask_login.current_user.is_authenticated:
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        privilage = request.form.get('privilage')

        if password == repassword :
            cursor.execute('UPDATE user_table SET privilage = ?, password = ? WHERE username = ?', (privilage,password,username))
            conn.commit()
            flash('You were successfully update password')
        else :
            flash('Password not saved. Try again.')

        print("{} done".format(password))
        print("{} done".format(repassword))
        print("{} done".format(privilage))
        print("{} done".format(username))

        return redirect(url_for('show_userprofile'))

@app.route('/deleteuser', methods=['POST'])
@flask_login.login_required
def deleteuser():

    if flask_login.current_user.is_authenticated:
        username = request.form.get('username')
        print ("deleteuser = {}".format(username))
        
        cursor.execute('SELECT * FROM data_table WHERE username=? ', (username,))
        entry = cursor.fetchone()

        if entry is not None:
            return redirect(url_for('show_userlist'))
            #cursor.execute('DELETE from data_table WHERE username = ?', (username,))
            #cursor.execute('DELETE from user_table WHERE username = ?', (username,))
            #conn.commit()

        else :
            #return redirect(url_for('show_userlist'))
            cursor.execute('DELETE from user_table WHERE username = ?', (username,))
            conn.commit()

        flash('You were successfully delete user')
            

        return redirect(url_for('update_admin'))
    

@app.errorhandler(400)
def custom400(error):
    response = jsonify({'message': error.description})
    return response, 400

def kill_server():
        print('You pressed Ctrl+C!')
        http_server.stop()
        sys.exit(0)



##### Data for Chart.js
import threading
lock = threading.Lock()

@app.route('/getFlightID', methods=['POST'])
def getFlightID():

    #date = request.get_data("date")
    #username = request.get_data("username")
    username = request.args.get('username')
    date = request.args.get('username')
    print("Date : {}".format(date))
    print("Username : {}".format(username))

    try:
        lock.acquire(True)
        cursor.execute('SELECT flight_id FROM flight WHERE date_taken LIKE ? AND username = ? ', (date+"%",username,))
        entry = cursor.fetchall()
        print("No of data for {} is {}".format(date,len(entry)))
    finally:
        lock.release()

    if entry:
        id = []
        for data in entry:
            flight_id = data['flight_id']
            id.append(flight_id)
        id = list(sorted(set(id)))
    return jsonify({'marker': json.dumps(id)}), 200

@app.route('/getFLightUsername', methods=['POST'])
def getFLightUsername():

    #username = request.get_data()
    username =  request.form['username']
    #username = request.args.get('username')
    print("Username : {}".format(username))

    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM flight WHERE username = ?', (username,))
        entry = cursor.fetchall()
        print("No of data for {} is {}".format(username,len(entry)))
    finally:
        lock.release()

    if entry:
        x=1
        marker={}
        lat = []
        lon = []
        dates = []
        dates2 = []
        img=[]
        total_row=len(entry)
        
        timetakeoff =[]
        timelanding = []

        for row in entry:
            imginv = []
            latinv = []
            loninv = []
            antypelist = []
            altinv = []
            
            flight_id = row['flight_id']
            altitude = row['altitude']
            latitude = row['latitude']
            longitude = row['longitude']
            date_taken = row['date_taken']
            user= row['username']
            image = row['loc_image']
            takeoff = row['takeoff']
            landing = row['landing']
            role = 0
            takeoff = (datetime.strptime(takeoff,'%H:%M:%S').time())
            landing = (datetime.strptime(landing,'%H:%M:%S').time())

            img.append(image)
            lat.append(float(row['latitude']))
            lon.append(float(row['longitude']))
            dates.append(str(datetime.strptime(date_taken,'%Y-%m-%d %H:%M:%S').date()))
            dates2.append(str(datetime.strptime(date_taken, '%Y-%m-%d %H:%M:%S').strftime('X%d-X%m-%Y').replace('X0','X').replace('X','')))

            try:
                lock.acquire(True)
                cursor.execute('SELECT * FROM data_table WHERE flight_id=?', (flight_id,))
                entry2 = cursor.fetchall()
            finally:
                lock.release()

            for i in entry2:

                #append data inv table
                image2 = i['image']
                lati = i['latitude']
                user2= i['username']
                loni = i['longitude']
                antype = i['type']
                alt = i['altitude']

                antenna = changeAntenna(antype) #change antenna name

                latinv.append(lati)
                loninv.append(loni)
                imginv.append(image2)
                antypelist.append(antenna)
                altinv.append(alt)

            #description = '<b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+'</span> ]</b><br><br><b>Lon/Lat : </b>'+str(longitude)+'&#176 , '+str(latitude)+'&#176'+'<br><b>Date/Time : </b>'+str(date_taken)+'<br><br><center><b>Fieldwork View </b><br><br>'+'<img style="height: 60%; width: 60%;" src="data:image/png;base64,'+str(image)+'" ismap /></center><br><form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;"><input type="hidden" value="'+str(imginv)+'" name="imginv"><input type="hidden" value="'+str(loninv)+'" name="loninv"> <input type="hidden" value="'+str(latinv)+'" name="latinv"> <input type="hidden" value="'+str(altinv)+'" name="altinv"> <input type="hidden" value="'+str(date_taken)+'" name="date"><input type="hidden" value="'+image+'" name="imag"> <input type="hidden" value="'+str(takeoff)+'" name="takeoff"><input type="hidden" value="'+str(landing)+'" name="landing"><input type="hidden" value="'+str(role)+'" name="role"> <input type="hidden" value="'+str(antypelist)+'" name="antypelist"> <input type="hidden" value="'+str(flight_id)+'" name="flightid"> <input style="width:50%;" type="submit" value="More Info"> </form>'
            description = ( '<center><b>[ Flight '+str(flight_id)+' Info by <span style="color:blue">'+user+' on '+str(date_taken)+'</span> ]</center><br>' +
                            '<table class="table">'+

                            '<thead>'+
                                '<tr>'+
                                '<th scope="col">Fieldwork Location</th>'+
                                '</tr>'+
                            '</thead>'+

                            '<tbody>'+
                                '<tr>'+
                                '<th><img class="img-thumbnail" src="data:image/png;base64,'+str(image)+'" ismap /></th>'
                                '</tr>'+
                            '</tbody>'+

                            '</table>'+

                            '<form accept-charset="UTF-8" action="/showinv" method="post" target="_blank" style="text-align: center; margin:3px;">'+
                            '<div class="form-group">'+
                            '<input type="hidden" value="'+str(imginv)+'" name="imginv">'+
                            '<input type="hidden" value="'+str(loninv)+'" name="loninv">'+
                            '<input type="hidden" value="'+str(latinv)+'" name="latinv">'+
                            '<input type="hidden" value="'+str(altinv)+'" name="altinv">'+
                            '<input type="hidden" value="'+str(date_taken)+'" name="date">'+
                            '<input type="hidden" value="'+image+'" name="imag">'+
                            '<input type="hidden" value="'+str(takeoff)+'" name="takeoff">'+
                            '<input type="hidden" value="'+str(landing)+'" name="landing">'+
                            '<input type="hidden" value="'+str(role)+'" name="role">'+
                            '<input type="hidden" value="'+str(antypelist)+'" name="antypelist">'+
                            '<input type="hidden" value="'+str(flight_id)+'" name="flightid">'+
                            '<input type="hidden" value="'+str(longitude)+'" name="lonnormal">'+
                            '<input type="hidden" value="'+str(latitude)+'" name="latnormal">'+
                            '<input class="form-control"  type="submit" value="More Info"> </form>'+
                            '</div>')

            objectname = 'object'+str(x)
            print("type marker {}".format(type(marker)))
            marker.update({objectname:{'lat':latitude, 'lng':longitude, 'description':description}})

            x+=1 
 
        print("marker {}".format(marker.keys()))
        print("len marker {}".format(len(marker)))
        return jsonify({'marker': json.dumps(marker)}), 200 

@app.route('/getUserData', methods=['GET'])
def getUserData():

    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM user_table WHERE privilage = 0 ')
        lenuser = cursor.fetchall()
        lenuser = len(lenuser)
    finally:
        lock.release()

    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM user_table WHERE privilage = 7 ')
        lenadmin = cursor.fetchall()
        lenadmin = len(lenadmin)
    finally:
        lock.release()

    return jsonify({'lenuserdata': lenuser, 'lenadmindata':lenadmin}), 200 

@app.route('/getAntennaData', methods=['GET'])
def getAntennaData():
    if flask_login.current_user.is_authenticated:
        username = flask_login.current_user.id

        cursor.execute('SELECT * FROM user_table WHERE status_log=? ', (username,))
        entry = cursor.fetchone()

        username=entry['username']
    
    dates = []



    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM flight WHERE username=? ', (username,))
        lenflight1 = cursor.fetchall()
        lenflight = len(lenflight1)
    finally:
        lock.release()

    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM data_table WHERE username=? ', (username,))
        lenasset = cursor.fetchall()
        lenasset = len(lenasset)
    finally:
        lock.release()
 
    return jsonify({'lenflight': lenflight, 'lenasset':lenasset}), 200 

@app.route('/getAllAntennaData', methods=['GET'])
def getAllAntennaData():

    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM flight ')
        lenflight1 = cursor.fetchall()
        lenflight = len(lenflight1)
    finally:
        lock.release()
    
    try:
        lock.acquire(True)
        cursor.execute('SELECT * FROM data_table')
        lenasset = cursor.fetchall()
        lenasset = len(lenasset)
    finally:
        lock.release()

    return jsonify({'lenflight': lenflight, 'lenasset':lenasset}), 200 

@app.route('/getTowerData', methods=['GET'])
def getTowerData():

    tottower = []
    tottownname = []
    tottower1=[]
    totstatename=[]
    countdata=[]
    statedata=[]
    try:
        lock.acquire(True)
        cursor.execute('SELECT SUM(count),statename FROM state GROUP BY statename')
        tott = cursor.fetchall()
        for row in tott:
            tottower.append([x for x in row]) # or simply data.append(list(row))
        tottower1 = np.array(tottower)
        rangetottower1 = len(tottower1)
        for i in range(rangetottower1):
            countdata.append(tottower1[i][0])
            statedata.append(tottower1[i][1])
    finally:
        lock.release()

    return jsonify({'tottowerdata': countdata,'totstatenamedata': statedata}), 200 

#Azmi Edit
def negeriloc():
    staterow = 0
    statelist1 = ['shah alam selangor','kuching sarawak','kota kinabalu sabah','putrajaya malaysia','kangar perlis','kuantan pahang','ipoh perak','georgetown penang malaysia','seremban negeri sembilan','gemencheh negeri sembilan','melaka malaysia','kuala lumpur malaysia','kota bharu kelantan','alor setar kedah','johor bahru johor','kuala terengganu']
    numstate = len(statelist1)
    telcodata = []
    entrydata = []

    try:
        lock.acquire(True)
        cursor.execute('Select * FROM state')
        entrydata = cursor.fetchall()
    finally:
        lock.release()

    totalentrydata = len(entrydata)

    if staterow == totalentrydata:

        for i in range(numstate):
            
            towerareaid = set()
            totalareaid = 0
            shortdatadisp = ""
            townname = ""

            locnew = statelist1[i]
            url = "https://nominatim.openstreetmap.org/search/"+locnew+"?format=json&addressdetails=1&limit=1"
            data = requests.get(url=url).text
            data = json.loads(data)
            
            for i in data:
                #bounding = ('{},{},{},{}'.format(i['boundingbox'][0],i['boundingbox'][1],i['boundingbox'][2],i['boundingbox'][3]))
                min5    = ('{}'.format(i['boundingbox'][0])) #minlat
                min6    = ('{}'.format(i['boundingbox'][1])) #minlon
                max5    = ('{}'.format(i['boundingbox'][2])) #maxlat
                max6    = ('{}'.format(i['boundingbox'][3])) #maxlon

                #minlat, minlon, maxlat, maxlon = "2.876833", "2.982444", "101.659687", "101.732682"
                
                disname = ('{}'.format(i['display_name']))
            
            cursor.execute('SELECT area,lon,lat,samples,created,updated FROM telco')
            teleco = cursor.fetchall()
            for row in teleco:
                telcodata.append([x for x in row])
            datalength = len(teleco)

            for j in range(datalength):
                data1 = telcodata[j]

                datadisp = data1[0]
                datalon = data1[1]
                datalat = data1[2]
                datasample = data1[3]
                datacreated = data1[4]
                dataupdated = data1[5]

                fldatalon=float(datalon)
                fldatalat=float(datalat)
                intdatasample = int(datasample)

                if datalat > min5 and datalat < min6 and datalon > max5 and datalon < max6 and datasample > "10" and datacreated == dataupdated :
                    towerareaid.add(datadisp)
                    totalareaid += 1

            if locnew == "shah alam selangor":
                shortdatadisp = "Selangor"
                townname = "Shah Alam"
            elif locnew == "kuching sarawak":
                shortdatadisp = "Sarawak"
                townname = "Kuching"
            elif locnew == "kota kinabalu sabah":
                shortdatadisp = "Sabah"
                townname = "Kota Kinabalu"
            elif locnew == "putrajaya malaysia":
                shortdatadisp = "Putrajaya"
                townname = "Putrajaya"
            elif locnew == "kangar perlis":
                shortdatadisp = "Perlis"
                townname = "Kangar"
            elif locnew == "kuantan pahang":
                shortdatadisp = "Pahang"
                townname = "Kuantan"
            elif locnew == "ipoh perak":
                shortdatadisp = "Perak"
                townname = "Ipoh"
            elif locnew == "georgetown penang malaysia":
                shortdatadisp = "Penang"
                townname = "Georgetown"
            elif locnew == "seremban negeri sembilan":
                shortdatadisp = "Negeri Sembilan"
                townname = "Seremban"
            elif locnew == "gemencheh negeri sembilan":
                shortdatadisp = "Negeri Sembilan"
                townname = "Gemencheh"
            elif locnew == "melaka malaysia":
                shortdatadisp = "Melaka"
                townname = "Melaka"
            elif locnew == "kuala lumpur malaysia":
                shortdatadisp = "Kuala Lumpur"
                townname = "Kuala Lumpur"
            elif locnew == "kota bharu kelantan":
                shortdatadisp = "Kelantan"
                townname = "Kota Bharu"
            elif locnew == "alor setar kedah":
                shortdatadisp = "Kedah"
                townname = "Alor Setar"
            elif locnew == "johor bahru johor":
                shortdatadisp = "Johor"
                townname = "Johor Bahru"
            elif locnew == "kuala terengganu":
                shortdatadisp = "Terengganu"
                townname = "Kuala Terengganu"

            cursor.execute('INSERT INTO state (negname,maxlat,minlat,maxlon,minlon,count,townname,statename) VALUES (?,?,?,?,?,?,?,?)', (locnew,max5,min5,max6,min6,len(towerareaid),townname,shortdatadisp))
            conn.commit() 
#azmi end edit


if __name__ == '__main__':
    init_db()
    
    http_server = WSGIServer((config['WEB-SERVER']['HOST'], int(config['WEB-SERVER']['PORT'])), app)
    print("\nRunning on {}:{}...\n".format(config['WEB-SERVER']['HOST'], config['WEB-SERVER']['PORT']))
    
    negeriloc()

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        kill_server()
