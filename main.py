from flask import Flask,render_template,request,url_for,session,redirect
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
app.config["SECRET_KEY"]="supercecretkey"
socketio=SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Users.sqlite3'
db=SQLAlchemy(app)

class Users(db.Model):
   id = db.Column('student_id', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   username = db.Column(db.String(100))  
   password = db.Column(db.String(100))
   email = db.Column(db.String(120))
   phone_number=db.Column(db.Integer)

   def __init__(self,name,username,password,email,phone_number):
        self.name=name
        self.username=username
        self.password=password
        self.email=email
        self.phone_number=phone_number


@app.route('/',methods=['POST','GET'])
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')


if __name__=='__main__':
    with app.app_context():
        db.create_all()
        socketio.run(app,debug=True)