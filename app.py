from flask import Flask, flash, redirect, request, render_template, url_for,Response
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import face_recognition
import cv2
import pickle
from datetime import datetime
import pandas as pd
from twilio.rest import Client
import pytz
import numpy as np
import os

app = Flask(__name__)
app.secret_key='abc'

IST = pytz.timezone('Asia/Kolkata')

app.config["SQLALCHEMY_BINDS"]={"std":"sqlite:///record/student.db","atd":"sqlite:///record/attendance.db"}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db=SQLAlchemy(app)

class Student(db.Model):
    __bind_key__='std'
    sno=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50),nullable=False)
    email=db.Column(db.String(50),nullable=False)
    mob=db.Column(db.String(50),nullable=False)
    pmob=db.Column(db.String(50),nullable=False)

class Attendance(db.Model):
    __bind_key__='atd'
    sno=db.Column(db.Integer,primary_key=True)
    pid=db.Column(db.String(50),nullable=False)
    pname=db.Column(db.String(50),nullable=False)
    date=db.Column(db.String(50),nullable=False)
    intime=db.Column(db.String(50),nullable=False)
    outtime=db.Column(db.String(50),default="")

    def __repr__(self) -> str:
        return f"{self.pid}--->{self.pname}--->{self.date}--->{self.intime}"

@app.route('/', methods =["GET", "POST"])
def index():
    return render_template("index.html")

@app.route('/option',methods =["GET", "POST"])
def option():
    return render_template('option.html')

@app.route('/tregistration')
def tregistration():
    return render_template('tregistration.html')

@app.route('/sregistration')
def sregistration():
    return redirect(url_for("register"))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/leave')
def leave():
    return render_template('leave.html')

@app.route('/leaves')
def leaves():
    return render_template('leaveappmsg.html')

@app.route('/nlogin', methods =["GET", "POST"])
def nlogin():
    return render_template('nlogin.html')

@app.route('/parent', methods =["GET", "POST"])
def parent():
    return redirect(url_for('login'))

@app.route('/login', methods =["GET", "POST"])
def login():
    email=""
    password=""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email=='admin@xyz.com' and password=='Abcd@1234':
            return render_template("adminl.html")
        elif email=='PHY101' and password=='Physics':
            return render_template("video.html")
        elif email=='CHEM101' and password=='Chemistry':
            return render_template("video.html")
        elif email=="" and password=="":
            return render_template("login.html")
        else:
            return render_template("login.html")
    return render_template("login.html")

@app.route('/index')
def attendance():
    attendance=Attendance.query.all()
    message()
    return render_template('attendance.html',attendance=attendance)

@app.route('/register', methods =["GET", "POST"])
def register():
    name=""
    if request.method=="POST":
        name=request.form.get("name").upper()
        email=request.form.get("email")
        mob=request.form.get("phone")
        pmob=request.form.get("pphone")
        st=Student(name=name,email=email,mob=mob,pmob=pmob)
        db.session.add(st)
        db.session.commit()
        if name!="":
            upload(name)
            return render_template('success.html')
    return render_template('register.html')

@app.route('/video',methods =["GET", "POST"])
def upload(name):
    name=name
    cam=cv2.VideoCapture(0)
    path="students"
    while(True and name!=""):
        try:
            os.makedirs(f"{path}/{name}")
        except:
            _,frame=cam.read()
            frame=cv2.flip(frame,1)
            cv2.imshow("IMAGE CAPTURING",frame)
            length=len(os.listdir(f"{path}/{name}"))
            if length<3:
                if cv2.waitKey(1) & 0xFF == ord('f'):
                    cv2.imwrite(f"{path}/{name}/{length+1}.jpg",frame)
                continue
            else:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()
                    os.system('python train.py')
                    return render_template('success.html')
    return render_template('success.html')

@app.route('/success',methods =["GET", "POST"])
def success():
    return render_template('success.html')

@app.route('/attendance')
def logout():
    return redirect(url_for("index"))

@app.route('/video',methods=["GET","POST"])
def video():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

def mark_attendance(id,name):
    database="record/attendance.db"
    conn=sqlite3.connect(database)
    df=pd.read_sql_query("Select * from Attendance",conn)
    if id!="" and name!="":
        dt=datetime.now(IST).strftime("%d/%m/%Y")
        if str(id) not in df["pid"].to_list():
            it=datetime.now(IST).strftime('%H:%M:%S')
            attd=Attendance(pid=id,pname=name,date=dt,intime=it)
            db.session.add(attd)
            db.session.commit()
        if str(id) in df["pid"].to_list():
            intimes=df["intime"].to_list()
            t1=intimes[df["pid"].to_list().index(str(id))]
            t2=datetime.now(IST).strftime('%H:%M:%S')
            if time_to_sec(t2)-time_to_sec(t1)>=15:
                job=Attendance.query.filter_by(pid=id).first()
                db.session.delete(job)
                attd=Attendance(pid=id,pname=name,date=dt,intime=t1,outtime=t2)
                db.session.add(attd)
                db.session.commit()

def message():
    # sid="Your Twilio sid"
    # auth_token="Your Twilio auth token"
    # client=Client(sid,auth_token)

    database1="record/attendance.db"
    database2="record/student.db"
    conn1=sqlite3.connect(database1)
    conn2=sqlite3.connect(database2)

    atd=pd.read_sql_query("Select * from Attendance",conn1)
    std=pd.read_sql_query("Select * from Student",conn2)
    pmob=pd.read_sql_query("Select pmob from Student",conn2)["pmob"]
    name=pd.read_sql_query("Select name from Student",conn2)["name"].tolist()
    pname=pd.read_sql_query("Select pname from Attendance",conn1)["pname"].tolist()
    atd["pmob"]=pmob
    l=pmob.tolist()

    for i in range(len(pname)):
        ind=name.index(pname[i])
        atd['pmob'][i]=l[ind]

    for i in range(len(pname)):
        if atd["outtime"][i]!="":
            to="+91"+pmob[i]
            msg=f"Your ward {atd['pname'][i]} has entered the class at {atd['intime'][i]} and left the class at {atd['outtime'][i]} on {atd['date'][i]}. Sent to {to}."
        else:
            to="+91"+pmob[i]
            msg=f"Your ward {atd['pname'][i]} has entered the class at {atd['intime'][i]} on {atd['date'][i]}.Sent to {to}."
        # resp=client.messages.create(body=msg,from_="+12182504162",to=to)
        # print(resp.sid)
        print(msg)

def time_to_sec(t):
    t=t.split(':')
    t[-1]=t[-1][0:2]
    h, m, s = map(int,t)
    return h * 3600 + m * 60 + s

def generate_frames():
    file=open("record/encodings.txt","rb")
    encoding=pickle.load(file)
    file2=open("record/names.txt","rb")
    names=pickle.load(file2)
    file3=open("record/ids.txt","rb")
    ids=pickle.load(file3)
    detName=""
    detId=""
    camera=cv2.VideoCapture(0)
    while True:
        success,frame=camera.read()
        if not success:
            break
        else:
            # frame=cv2.flip(frame,1)
            process_frame=True
            if process_frame:
                small_frame=cv2.resize(frame,(0,0),fx=0.25,fy=0.25)
                name=""
                rgb_small_frame=small_frame[:,:,::-1] #converting bgr(which opencv uses) to rgb
                faces=face_recognition.face_locations(rgb_small_frame)
                encodes=face_recognition.face_encodings(rgb_small_frame,faces)
                for en in encodes:
                    matches=face_recognition.compare_faces(encoding,en)
                    face_distances = face_recognition.face_distance(encoding,en)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = names[best_match_index]
                        id=ids[best_match_index]
            process_frame=not process_frame
            detectedName=[]
            detectedId=[]
            
            for(top,right,bottom,left) in faces:
                top=top*4
                right=right*4
                bottom=bottom*4
                left=left*4
                frame=cv2.rectangle(frame,(left,top),(right,bottom),(0,0,255),2)
                if name !="":
                    detName=name.split()[0]
                    detId=id
                frame=cv2.rectangle(frame,(left,bottom),(right,bottom+55),(0,255,0),cv2.FILLED)
                frame=cv2.putText(frame,detName,(left,bottom+25),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,0),2)
                frame=cv2.putText(frame,str(detId),(left,bottom+50),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,0),1)
                mark_attendance(detId,name)
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()

        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__=='__main__':
    app.run()
