from flask import Blueprint,render_template,request,redirect,session
from config.db import mysql

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute(  '''  SELECT * FROM users  WHERE email=%s  AND password=%s ''',   (email, password) )
        user = cursor.fetchone()
        if user:
            cursor.execute( '''INSERT INTO login_activity (name, email, role)  VALUES(%s,%s,%s) ''',
                ( user[1],
                    user[2],
                    user[5] ) )
            mysql.connection.commit()
            session['user_id'] = user[0]
            session['role'] = user[5]
            if user[5] == 'Admin':
                return redirect('/admin/dashboard')

            elif user[5] == 'Team Member':
                return redirect('/team/dashboard')

            elif user[5] == 'Agent':
                return redirect('/agent/dashboard')

    return render_template(  'auth/login.html' )


@auth.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@auth.route('/change-password',
methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        cursor = mysql.connection.cursor()
        cursor.execute(  ''' SELECT * FROM users
            WHERE id=%s
            AND password=%s ''',
            (  session['user_id'],
                old_password   ) )
        user = cursor.fetchone()
        if user:
            if new_password == confirm_password:
                cursor.execute(  ''' UPDATE users
                  SET password=%s WHERE id=%s ''', (  new_password,   session['user_id']  )  )
                mysql.connection.commit()

                return redirect('/logout')
    return render_template(  'auth/change_password.html' )


@auth.route('/contact',
methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        cursor = mysql.connection.cursor()
        cursor.execute( ''' INSERT INTO contact_messages (name, email, subject, message) VALUES(%s,%s,%s,%s) ''',
            ( name,  email, subject, message   ) )
        mysql.connection.commit()

        return redirect('/contact')
    return render_template(  'contact.html'  )


@auth.route('/forgot-password',
methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        cursor = mysql.connection.cursor()
        cursor.execute( ''' UPDATE users  SET password=%s   WHERE email=%s ''', ( new_password,    email  ) )

        mysql.connection.commit()
        return redirect('/')
    return render_template('auth/forgot_password.html' )


@auth.route('/')
def home():
    return render_template(
        'home.html' )


@auth.route('/about')
def about():
    return render_template(  'about.html' )


@auth.route('/register',
methods=['GET', 'POST'])

def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        role = request.form['role']
        cursor = mysql.connection.cursor()
        cursor.execute( ''' INSERT INTO users (name, email, mobile, password, role,status) VALUES(%s,%s,%s,%s,%s,%s) ''',
                        ( name, email, mobile,  password, role,  'Active'  ) )
        mysql.connection.commit()
        return redirect('/')
    return render_template(  'auth/register.html' )