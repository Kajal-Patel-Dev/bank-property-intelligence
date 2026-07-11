from flask import Flask
from flask_login import LoginManager,current_user
from config.db import mysql

app = Flask(__name__)
app.secret_key = 'super_secret_key_123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ka@960491'
app.config['MYSQL_DB'] = 'bank_real_estate'

mysql.init_app(app)

login_manager = LoginManager()
login_manager .init_app(app)

@login_manager.user_loader
def load_user(user_id):
    cur=mysql.connection.cursor()
    cur.execute("select * from users where id=%s", (user_id))
    user=cur.fetchone()
    print("user object:",user)
    cur.close()
    return user

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


from routes.auth import auth
from routes.admin import admin
from routes.team import team
from routes.agent import agent


app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(team)
app.register_blueprint(agent)

if __name__ == '__main__':
    app.run(debug=True)