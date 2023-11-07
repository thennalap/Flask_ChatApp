from flask import Flask,render_template,request,url_for,session,redirect,flash
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from flask_migrate import Migrate
import re

app=Flask(__name__)
app.config["SECRET_KEY"]="supercecretkey"
socketio=SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Users.sqlite3'
db=SQLAlchemy(app)
migrate = Migrate(app, db)

class Users(db.Model):
   id = db.Column('student_id', db.Integer, primary_key = True)
   name = db.Column(db.String(100))
   username = db.Column(db.String(100))  
   password = db.Column(db.String(128))
   email = db.Column(db.String(120))
   phone_number=db.Column(db.Integer)
   

#    @property
#    def password_hash(self):
#        raise AttributeError('Password is not a readable attribute')
   
#    @password_hash.setter
#    def password_hash(self,password):
#        self.password=generate_password_hash(password)
    
   def verify_password(self,password):
       return check_password_hash(self.password,password)

   def __init__(self,name,username,password,phone_number,email):
        self.name=name
        self.username=username
        self.password=password        
        self.phone_number=phone_number
        self.email=email
       


@app.route('/',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        print(username,password)
    return render_template('login.html')

@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method=='POST':
        name=request.form['name']
        username=request.form['username']
        phone_number=request.form['phone_number']
        email=request.form['email']
        password=request.form['password']
        confirm_password=request.form['confirm_password']

        #Regex for password and email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        password_pattern=r"^(?=.*\d)(?=.*[\W_]).*$"

        #check if username already taken
        user_exists=Users.query.filter_by(username=username).first()

         #check if email already exists
        email_exists=Users.query.filter_by(email=email).first()

        #check if phone number already exists
        phone_number_exists=Users.query.filter_by(phone_number=phone_number).first()
        

        #Password and confirm password checking
        if password!=confirm_password:
            flash("Password and Confirm Password must be same")
            return redirect(url_for('signup'))
        elif not re.fullmatch(pattern,email):
            flash("Enter a valid email")
            return redirect(url_for('signup'))
        elif not re.fullmatch(password_pattern,password):
            flash("Password must contain atleast one digit and one symbol")
            return redirect(url_for('signup'))
        elif user_exists:
            flash("Username already taken. Please select another")
            return redirect(url_for('signup'))
        elif phone_number_exists:
            flash("Phne Number already exists. Please use another")
            return redirect(url_for('signup'))
        elif email_exists:
            flash("Email already exists. Please use another")
            return redirect(url_for('signup'))

        else:
            #Password Hashing 
            hashed_password = generate_password_hash(password)
            user=Users(name,username,hashed_password,phone_number,email)
            db.session.add(user)
            db.session.commit()
            flash("Registered Succesfully")
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/home')
def chat_home():
    return render_template("chat_home.html")

@app.route('/view')
def view():    
    return render_template('view.html',values=Users.query.all())

if __name__=='__main__':
    with app.app_context():
        db.create_all()
        socketio.run(app,debug=True)

