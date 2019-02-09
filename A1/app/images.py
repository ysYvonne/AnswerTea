from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp

from app.users import sign, verify

import mysql.connector

from app.config import db_config

import os

from wand.image import Image

webapp.secret_key = '\x80\xa9s*\x12\xc7x\xa9d\x1f(\x03\xbeHJ:\x9f\xf0!\xb1a\xaa\x0f\xee'


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


@webapp.route('/images/upload', methods=['POST'])
# upload new images and save their filenames in the database.
def images_upload():

    users_id = session.get('username')

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', str(users_id))

    cnx = get_db()
    cursor = cnx.cursor()

    for upload in request.files.getlist("file"):
        filename = upload.filename
        path = os.path.join(ROOT,filename)
        upload.save(path)
        query = ''' INSERT INTO images (users_id,filename)
                           VALUES (%s,%s)'''
        cursor.execute(query, (users_id,filename))

        # create thumbnails
        filename_thumb = filename + '_thumbnail.png'
        path_thumb_full = os.path.join(ROOT, filename_thumb)

        # create rotated transformations path
        filename_rotated = filename + '_rotated.png'
        path_rotated_full = os.path.join(ROOT, filename_rotated)

        # create flopped transformations path
        filename_flopped = filename + '_flopped.png'
        path_flopped_full = os.path.join(ROOT, filename_flopped)

        # created gray-scale transformations path
        filename_gray = filename + '_gray.png'
        path_gray_full = os.path.join(ROOT, filename_gray)

        # generate all images and save
        with Image(filename=path) as img:
            with img.clone() as thumb:
                size = thumb.width if thumb.width < thumb.height else thumb.height
                thumb.crop(width=size, height=size, gravity='center')
                thumb.resize(128, 128)
                thumb.format = "png"
                thumb.save(filename=path_thumb_full)

            with img.clone() as rotated:
                rotated.rotate(135)
                rotated.format = "png"
                rotated.save(filename=path_rotated_full)

            with img.clone() as flopped:
                flopped.flop()
                flopped.format = "png"
                flopped.save(filename=path_flopped_full)

            with img.clone() as gray:
                gray.type = 'grayscale'
                gray.format = "png"
                gray.save(filename=path_gray_full)

    cnx.commit()
    return redirect(url_for('user_home'))


@webapp.route('/images/trans/<filename>', methods=['GET'])
# show the transformations of a specific image.
def images_trans(filename):
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    return render_template("images/trans.html",title="Transformations", filename=filename)


@webapp.route('/trans/<filename>', methods=['GET','POST'])
# display thumbnails of a specific account
def send_image_trans(filename):
    users_id = session.get('username')
    path = os.path.join(str(users_id), filename)
    return send_from_directory("images", path)


@webapp.route('/test/FileUpload', methods=['GET'])
# display an HTML form that allows TAs to upload pictures using script
def script():
    return render_template("script.html",title="uploadForm")


@webapp.route('/test/FileUpload', methods=['POST'])
# let TAs to automatically upload photos to populate their account
def script_upload():
    username = request.form.get('userID',"")
    password = request.form.get('password',"")

    error = False

    if username == "" or password== "" :
        error=True
        error_msg="Error: All fields are required!"

    else :
        cnx = get_db()
        cursor = cnx.cursor()

        query = '''SELECT id, password FROM users
                          WHERE username = %s'''
        cursor.execute(query,(username,))
        row = cursor.fetchone()

        if row is None :
            error=True
            error_msg="Error: User Does not exist!"

        elif not verify(password, bytes(row[1], 'utf-8')) :
            error=True
            error_msg="Error: password does not match!"

    if error :
        return render_template("script.html",title="uploadForm",
                    error_msg=error_msg, username=username)

    users_id = row[0]

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', str(users_id))

    cnx = get_db()
    cursor = cnx.cursor()

    for upload in request.files.getlist("uploadedfile"):
        filename = upload.filename
        path = os.path.join(ROOT,filename)
        upload.save(path)
        query = ''' INSERT INTO images (users_id,filename)
                           VALUES (%s,%s)'''
        cursor.execute(query, (users_id,filename))

        # create thumbnails
        filename_thumb = filename + '_thumbnail.png'
        path_thumb_full = os.path.join(ROOT, filename_thumb)

        # create rotated transformations path
        filename_rotated = filename + '_rotated.png'
        path_rotated_full = os.path.join(ROOT, filename_rotated)

        # create flopped transformations path
        filename_flopped = filename + '_flopped.png'
        path_flopped_full = os.path.join(ROOT, filename_flopped)

        # created gray-scale transformations path
        filename_gray = filename + '_gray.png'
        path_gray_full = os.path.join(ROOT, filename_gray)

        # generate all images and save
        with Image(filename=path) as img:
            with img.clone() as thumb:
                size = thumb.width if thumb.width < thumb.height else thumb.height
                thumb.crop(width=size, height=size, gravity='center')
                thumb.resize(128, 128)
                thumb.format = "png"
                thumb.save(filename=path_thumb_full)

            with img.clone() as rotated:
                rotated.rotate(135)
                rotated.format = "png"
                rotated.save(filename=path_rotated_full)

            with img.clone() as flopped:
                flopped.flop()
                flopped.format = "png"
                flopped.save(filename=path_flopped_full)

            with img.clone() as gray:
                gray.type = 'grayscale'
                gray.format = "png"
                gray.save(filename=path_gray_full)

    cnx.commit()
    msg = 'Upload completed!'

    return render_template("script.html",title="uploadForm",
                msg=msg,username=username,password=password)
