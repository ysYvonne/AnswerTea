from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp
import hashlib
from hmac import compare_digest

import mysql.connector

from app.config import db_config

from passlib.hash import pbkdf2_sha256
import os
import random

webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'

SECRET_KEY = b'pseudo randomly generated secret key'
AUTH_SIZE = 16


def sign(pwd):  # sign(password1)
    #h = hashlib.md5()
    #h.update(bytes(cookie, 'utf-8'))
    #return h.hexdigest().encode('utf-8')
    hash = pbkdf2_sha256.encrypt((bytes(pwd, 'utf-8')), salt_size=16)
    print (hash)
    return hash


def verify(pwd, sig):
    # good_sig = sign(pwd)
    # return compare_digest(good_sig, sig)
    return pbkdf2_sha256.verify(pwd, sig)


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@webapp.route('/signup', methods=['GET'])
# Display an HTML form that allows user to sign up.
def signup():
    return render_template("user/signup.html",title="New User")


@webapp.route('/signup', methods=['POST'])
# Create a new account and save it in the database.
def signup_save():
    username = request.form.get('username',"")
    password1 = request.form.get('password1',"")
    password2 = request.form.get('password2',"")

    error = False

    if username == "" or password1== "" or password2== "" :
        error=True
        error_msg="Error: All fields are required!"

    elif len(password1) > 8 or len(password1)<6 :
        error=True
        error_msg = "Error: Password must be between 6 to 8 characters!"

    elif password1 != password2 :
        error=True
        error_msg="Error: The re-typed password does not match your first entry!"

    else :
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''SELECT * FROM user
                          WHERE username = %s'''
        cursor.execute(query,(username,))
        row = cursor.fetchone()

        if row is not None :
            error=True
            error_msg="Error: User name already exists!"


    if error:
        return render_template("user/signup.html",title="New User",error_msg=error_msg, username=username)

    cnx = get_db()
    cursor = cnx.cursor()

    query = ''' INSERT INTO user (username,password)
                       VALUES (%s, %s)'''

    cursor.execute(query,(username,sign(password1)))
    cnx.commit()

    session['authenticated'] = True

    query = '''SELECT id FROM user
                      WHERE username = %s'''
    cursor.execute(query,(username,))
    row = cursor.fetchone()
    session['username'] = row[0]

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    path = os.path.join(ROOT, str(row[0]))
    os.makedirs(path)

    return redirect(url_for('login'))

@webapp.route('/main', methods=['POST'])
def auto_signup():
    username = ''.join( random.sample("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", 8))
    password = ''.join( random.sample("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_1234567890", 6))


    cnx = get_db()
    cursor = cnx.cursor()

    query =  "INSERT INTO user (username,password) VALUES (%s, %s)"
    cursor.execute(query, (username, sign(password)))
    cnx.commit()

    session['authenticated'] = True

    session['username'] = username

    query = '''SELECT id, password FROM user
                              WHERE username = %s'''
    cursor.execute(query, (username,))
    row = cursor.fetchone()

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    path = os.path.join(ROOT, str(row[0]))
    os.makedirs(path)


    return render_template(('user/login.html'), username = username, password = password)


@webapp.route('/login',methods=['GET'])
# Display an HTML form that allows user to log in.
def login():
    return render_template("user/login.html",title="Log in")


@webapp.route('/login_submit',methods=['POST'])
###################################################
def login_submit():
    username = request.form.get('username',"")
    password = request.form.get('password',"")

    error = False

    if username == "" or password== "" :
        error=True
        error_msg="Error: All fields are required!"

    else :
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''SELECT id, password FROM user
                          WHERE username = %s'''
        cursor.execute(query,(username,))
        row = cursor.fetchone()

        if row is None or not verify(password, bytes(row[1], 'utf-8')):
            error=True
            error_msg="Error: Username doesn't exist or Password doesn't match!"

        # elif not verify(password, bytes(row[1], 'utf-8')) :
        #     error=True
        #     error_msg="Error: password does not match!"

    if error :
        return render_template("user/login.html",title="Log in",error_msg=error_msg, username=username)

    session['authenticated'] = True
    session['username'] = row[0]

    flag = True

    return redirect(url_for('user_home', flag=flag))


@webapp.route('/home/<flag>', methods=['GET'])
def user_home(flag):
    flag = flag
    error_msg = ''
    if flag == 'False':
        error_msg = 'Cannot upload more than 100 pictures!'
    # error_msg = ''
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    user_id = session.get('username')

    cnx = get_db()
    cursor = cnx.cursor()

    query = '''SELECT image_name FROM user_has_images
                WHERE user_id = %s    
                   '''

    cursor.execute(query,(user_id,))

    return render_template("images/home.html",title="User Home", cursor=cursor, error_msg = error_msg)


@webapp.route('/show/<filepath>', methods=['GET'])
def send_image(filepath):
    filepath_thumb = filepath + '_thumbnail.png'
    user_id = session.get('username')
    #path = os.path.join(str(user_id), filepath_thumb)
    path = os.path.join('images',str(user_id))
    # return the path of the pictuer to display
    return send_from_directory(path, filepath_thumb)


@webapp.route('/logout',methods=['POST'])
# Clear the session when user want to log out.
def logout():
    session.clear()
    return redirect(url_for('main'))
