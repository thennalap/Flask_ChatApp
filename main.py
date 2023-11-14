from flask import Flask,render_template,request,url_for,session,redirect,flash,jsonify
from flask_socketio import SocketIO,join_room,leave_room,send
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from flask_migrate import Migrate
import re
import random
from datetime import datetime

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
   chat_room_id=db.Column(db.String(100))
    
   def verify_password(self,password):
       return check_password_hash(self.password,password)

   def __init__(self,name,username,password,phone_number,email,chat_room_id):
        self.name=name
        self.username=username
        self.password=password        
        self.phone_number=phone_number
        self.email=email
        self.chat_room_id=chat_room_id

class Messages(db.Model):
    id = db.Column('message_id', db.Integer, primary_key = True)
    from_user=db.Column(db.String(100))
    to_user=db.Column(db.String(100))
    content=db.Column(db.String(1000))
    message_time=db.Column(db.DateTime)

    def __init__(self,from_user,to_user,content,message_time):
        self.from_user=from_user
        self.to_user=to_user
        self.content=content
        self.message_time=message_time

    def to_dict(self):
        data = {
            "id" : self.id,
            "from_user" : self.from_user,
            "to_user" : self.to_user,
            "content" : self.content,
            "message_time" : self.message_time
        }
        return data


@app.route('/',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password_entered=request.form['password']
        # Checking username entered if exists or not
        user_exists=Users.query.filter_by(username=username).first()

        # If user exists checking the passwords, with the entered password and hashed password using check_password _hash.
        if user_exists:            
            print("user exists")
            name=user_exists.name
            username=user_exists.username
            password_hashed=user_exists.password
            checking_password=check_password_hash(password_hashed,password_entered)
            if checking_password == True:
                session['username']=username
                return redirect(url_for('chat_home'))
            else:
                flash("Invalid Password")
                return redirect(url_for('login'))
                
        else:
            flash("Invalid Username")
            return redirect(url_for('login'))
        
    else:
        if "username" in session:
            return redirect(url_for('chat_home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username',None)
        flash("Log Out Successfully")   
    return redirect(url_for('login'))

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
        

        # Password and confirm password checking
        # if password!=confirm_password:
        #     flash("Password and Confirm Password must be same")
        #     return redirect(url_for('signup'))
        if not re.fullmatch(pattern,email):
            flash("Enter a valid email")
            return redirect(url_for('signup'))
        elif not re.fullmatch(password_pattern,password):
            flash("Password must contain atleast one digit and one symbol")
            return redirect(url_for('signup'))
        elif user_exists:
            flash("Username already taken. Please select another")
            return redirect(url_for('signup'))
        elif phone_number_exists:
            flash("Phone Number already exists. Please use another")
            return redirect(url_for('signup'))
        elif email_exists:
            flash("Email already exists. Please use another")
            return redirect(url_for('signup'))

        else:
            #Password Hashing 
            hashed_password = generate_password_hash(password)
            chat_room_id=random.randint(1001,9999)
            user=Users(name,username,hashed_password,phone_number,email,chat_room_id)
            db.session.add(user)
            db.session.commit()
            flash("Registered Succesfully")
            return redirect(url_for('login'))
    return render_template('signup.html')



@app.route('/home',methods=['POST','GET'])
def chat_home():
    if "username" in session:
        from_username=session['username']
        user_exists=Users.query.filter_by(username=from_username).first()    
        other_users=Users.query.filter(Users.username != from_username).all()
        return render_template('chat_home.html',users=other_users,login_user=user_exists)
    else:
        flash("You are not logged in!!")
        return redirect(url_for('login'))

@app.route('/getMessages/<string:to_username>',methods=['POST','GET'])
def get_all_messages(to_username):
    # to_username = request.json.get('to_username')
    from_username = session['username']
    msgs=Messages.query.filter(Messages.from_user.in_([to_username,from_username]),Messages.to_user.in_([to_username,from_username])).all()  
    all_messages = []
    for msg in msgs:
        all_messages.append(msg.to_dict())  
    return jsonify(all_messages)



@socketio.on('connect')
def handle_connect():
    print("Client Connected")
    from_username=session['username']
    from_user=Users.query.filter_by(username=from_username).first()
    from_user_room_id=from_user.chat_room_id
    print(from_user_room_id,"iddddddddddd")
    join_room(from_user_room_id)
    print("room joined")
    
    

@socketio.on('message')
def handle_message(payload):    
    from_username = payload['from_username']
    to_username = payload['to_username']
    message = payload['message']
    now = datetime.now()
    # message_date_time = now.strftime("%d/%m/%Y %H:%M:%S")
    from_user=Users.query.filter_by(username=from_username).first()
    from_user_room_id=from_user.chat_room_id
    to_user=Users.query.filter_by(username=to_username).first()
    to_user_room_id=to_user.chat_room_id
    msg=Messages(from_username,to_username,message,now)
    db.session.add(msg)
    db.session.commit()
    print("Message added Succesfully")  
    print(message,from_username,to_username)
    chat_message={
        'message':message,
        'from_username':from_username,
        'to_username':to_username

    }    
    send(chat_message,broadcast=True,room=from_user_room_id)
    send(chat_message,broadcast=True,room=to_user_room_id)

    

@socketio.on('disconnect')
def handle_disconnect():
    from_username=session['username']
    leave_room(from_username)


if __name__=='__main__':
    with app.app_context():
        db.create_all()
        socketio.run(app,debug=True)

