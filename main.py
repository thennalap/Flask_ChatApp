from flask import Flask,render_template,request,url_for,session,redirect
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
app=Flask(__name__)
app.config["SECRET_KEY"]="supercecretkey"
socketio=SocketIO(app)

@app.route('/',methods=['POST','GET'])
def login():
    return render_template('login.html')


if __name__=='__main__':
    socketio.run(app,debug=True)