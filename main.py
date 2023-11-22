from flask import Flask,render_template,request,url_for,session,redirect,flash,jsonify
from flask_socketio import SocketIO, emit,join_room,leave_room, rooms,send
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
    read_messages=db.Column(db.Boolean)  # When read the message it will set to True for unread it will be False

    def __init__(self,from_user,to_user,content,message_time,read_messages):
        self.from_user=from_user
        self.to_user=to_user
        self.content=content
        self.message_time=message_time
        self.read_messages=read_messages

    def to_dict(self):
        self.message_time=self.message_time.strftime("%d-%m-%Y %H:%M")
        data = {
            "id" : self.id,
            "from_user" : self.from_user,
            "to_user" : self.to_user,
            "content" : self.content,
            "message_time" : self.message_time,
            "read_messages":self.read_messages
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
    
    

@app.route('/getMessages/',methods=['POST','GET'])
def get_all_messages():
    to_username = request.json.get('to_username')
    from_username = session['username']
    msgs=Messages.query.filter(Messages.from_user.in_([to_username,from_username]),Messages.to_user.in_([to_username,from_username])).all()  
    all_messages = []
    for msg in msgs:
        msg_dict = msg.to_dict()
        all_messages.append(msg_dict)  
    return jsonify(all_messages)

@app.route('/getUnreadMessagesCount/',methods=['POST','GET'])
def get_unread_messages_count():
    from_username=session['username']
    unread_messages_list=[]
    other_users=Users.query.filter(Users.username != from_username).all()  
    message_counts={ }
    for each_other_user in other_users:
        unread_msg_count=Messages.query.filter(Messages.from_user.in_([each_other_user.username]),Messages.to_user.in_([from_username]),Messages.read_messages==False).count()
        print(unread_msg_count,"messaggeeeeee from",each_other_user.username)
        message_counts[each_other_user.username]=unread_msg_count
    print(message_counts)
    return jsonify(message_counts)


@app.route('/setStatus/',methods=['POST','GET'])
def set_status():
    message_id=request.json.get('message_id')
    message_id_dict = {'message_id': message_id}
    current_message = Messages.query.get(message_id)
    current_message.read_messages = True
    db.session.commit()
    return jsonify(message_id_dict)

@app.route('/mark_messages_as_read/',methods=['POST','GET'])
def mark_messages_as_read():
    to_username=request.json.get('to_username')
    from_username=session['username']
    unread_data=request.json.get('unread_data') 
    messages=Messages.query.filter(Messages.from_user==to_username,Messages.to_user==from_username,Messages.read_messages==False).all()
    for message in messages:
        message.read_messages=True
    db.session.commit()
    for key in unread_data:
        if key == to_username:
            unread_data[key]=0
    return jsonify(unread_data)

 
@socketio.on('connect')
def handle_connect():
    print("Client Connected")
    from_username=session['username']
    from_user=Users.query.filter_by(username=from_username).first()
    from_user_room_id=from_user.chat_room_id
    print(f"Connected user: {from_username}")
    join_room(from_user_room_id)
    print("room joined")
    print(f"Room joined: {from_user_room_id}")


    
    

@socketio.on('message')
def handle_message(payload):    
    from_username = payload['from_username']
    to_username = payload['to_username']
    message = payload['message']
    now = datetime.now()
    formatted_time=now.strftime("%d-%m-%Y %H:%M")

    #select from_user room id     
    from_user=Users.query.filter_by(username=from_username).first()
    from_user_room_id=from_user.chat_room_id

    #select to_user room id
    to_user=Users.query.filter_by(username=to_username).first()
    to_user_room_id=to_user.chat_room_id
    
    #setting read messages to False
    read_message=False

    #saving message to database
    msg=Messages(from_username,to_username,message,now,read_message)
    db.session.add(msg)
    db.session.commit()
    print("Message added Succesfully")  
    
    chat_message={
        'content':message,
        'from_user':from_username,
        'to_user':to_username,
        'message_time':formatted_time,
        'message_id':msg.id,
        'self' : True
    }
    chat_message_2={
        'content':message,
        'from_user':from_username,
        'to_user':to_username,
        'message_time':formatted_time,
        'message_id':msg.id,
        'self' :False
    }
    send(chat_message,to=from_user_room_id)
    send(chat_message_2,to=to_user_room_id)

@socketio.on('mark_messages_as_read')
def handle_messages_read(payload):
    from_username=session['username']
    to_username=payload['to_username']
    unread_data=payload['unread_data']
    print(unread_data)
    #select from_user room id     
    from_user=Users.query.filter_by(username=from_username).first()
    from_user_room_id=from_user.chat_room_id

    #select to_user room id
    to_user=Users.query.filter_by(username=to_username).first()
    to_user_room_id=to_user.chat_room_id

    messages=Messages.query.filter(Messages.from_user==to_username,Messages.to_user==from_username).all()

    for message in messages:
        message.read_messages=True
    db.session.commit()
    
    # Emit an event back to the client to update the UI
    emit("read_messages", {
        "to_username": to_username,
        "unread_messages_count": 0
    }, broadcast=True)

    

@socketio.on('disconnect')
def handle_disconnect():
    from_username=session['username']
    from_user=Users.query.filter_by(username=from_username).first()
    from_user_room_id=from_user.chat_room_id
    leave_room(from_user_room_id)
    print("leaved room")


@app.route('/forgot_password',methods=['POST','GET'])
def forgot_password():
    if request.method=='POST':
        username=request.form['username']
        phone_number=request.form['phone_number']
        email=request.form['email']
        user_exists=Users.query.filter_by(username=username,phone_number=phone_number,email=email).first()
        if user_exists:
            return render_template('forgot_password.html', username=username,phone_number=phone_number,email=email, show_password_form=True)
        else:
            flash('Invalid credentials. Please check your username, phone number, and email.')
            return render_template('forgot_password.html', show_password_form=False)
    return render_template('forgot_password.html')

@app.route("/reset_password",methods=['POST','GET'])
def reset_password():
    if request.method=='POST':    
        username = request.form['username']
        phone_number = request.form['phone_number']
        email = request.form['email']   
        new_password=request.form['new_password']        
        password_pattern=r"^(?=.*\d)(?=.*[\W_]).*$"       
        if not re.fullmatch(password_pattern,new_password):
            flash("Password must contain atleast one digit and one symbol")
            return render_template('forgot_password.html')  
        else:
            hashed_password = generate_password_hash(new_password)
            user=Users.query.filter_by(username=username, email=email, phone_number=phone_number).first()
            user.password=hashed_password
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('forgot_password.html')  
 
   


if __name__=='__main__':
    with app.app_context():
        db.create_all()
        socketio.run(app,debug=True)

