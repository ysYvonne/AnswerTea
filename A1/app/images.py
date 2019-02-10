from flask import render_template, session, redirect, url_for, request, g, send_from_directory
from app import webapp

from app.user import sign, verify

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
# upload new images and save their filepaths in the database.
def images_upload():

    user_id = session.get('username')

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', str(user_id))

    cnx = get_db()
    cursor = cnx.cursor()
    cursor1 = cnx.cursor()
    cursor2 = cnx.cursor()

    for upload in request.files.getlist("file"):
        filepath = upload.filename
        path = os.path.join(ROOT,filepath)
        upload.save(path)

        query1 = ''' INSERT INTO images (filepath)
                           VALUES (%s)'''
        cursor.execute(query1, (filepath,))

        query2 =  '''SELECT id FROM images
                     WHERE filepath = %s'''
        cursor1.execute(query2, (filepath,))

        query3 = ''' INSERT INTO user_has_images (user_id,images_id)
                           VALUES (%s,%s)'''
        row = cursor.fetchone()

        cursor2.execute(query3, (user_id, row[0]))

        # create thumbnails
        filepath_thumb = filepath + '_thumbnail.png'
        path_thumb_full = os.path.join(ROOT, filepath_thumb)

        # create rotated transformations path
        filepath_rotated = filepath+ '_rotated.png'
        path_rotated_full = os.path.join(ROOT, filepath_rotated)

        # create flopped transformations path
        filepath_flopped = filepath + '_flopped.png'
        path_flopped_full = os.path.join(ROOT, filepath_flopped)

        # created gray-scale transformations path
        filepath_gray = filepath + '_gray.png'
        path_gray_full = os.path.join(ROOT, filepath_gray)

        # generate all images and save
        with Image(filepath=path) as img:
            with img.clone() as thumb:
                size = thumb.width if thumb.width < thumb.height else thumb.height
                thumb.crop(width=size, height=size, gravity='center')
                thumb.resize(128, 128)
                thumb.format = "png"
                thumb.save(filepath=path_thumb_full)

            with img.clone() as rotated:
                rotated.rotate(135)
                rotated.format = "png"
                rotated.save(filepath=path_rotated_full)

            with img.clone() as flopped:
                flopped.flop()
                flopped.format = "png"
                flopped.save(filepath=path_flopped_full)

            with img.clone() as gray:
                gray.type = 'grayscale'
                gray.format = "png"
                gray.save(filepath=path_gray_full)

    cnx.commit()
    return redirect(url_for('user_home'))


@webapp.route('/images/trans/<filepath>', methods=['GET'])
# show the transformations of a specific image.
def images_trans(filepath):
    if 'authenticated' not in session:
        return redirect(url_for('login'))

    return render_template("images/trans.html",title="Transformations", filepath=filepath)


@webapp.route('/trans/<filepath>', methods=['GET','POST'])
# display thumbnails of a specific account
def send_image_trans(filepath):
    user_id = session.get('username')
    path = os.path.join(str(user_id), filepath)
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

        query = '''SELECT id, password FROM user
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

    user_id = row[0]

    ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', str(user_id))

    cnx = get_db()
    cursor = cnx.cursor()

    for upload in request.files.getlist("uploadedfile"):
        filepath = upload.filepath
        path = os.path.join(ROOT,filepath)
        upload.save(path)
        query = ''' INSERT INTO images (id,filepath)
                           VALUES (%s,%s)'''
        cursor.execute(query, (user_id,filepath))

        # create thumbnails
        filepath_thumb = filepath + '_thumbnail.png'
        path_thumb_full = os.path.join(ROOT, filepath_thumb)

        # create rotated transformations path
        filepath_rotated = filepath + '_rotated.png'
        path_rotated_full = os.path.join(ROOT, filepath_rotated)

        # create flopped transformations path
        filepath_flopped = filepath + '_flopped.png'
        path_flopped_full = os.path.join(ROOT, filepath_flopped)

        # created gray-scale transformations path
        filepath_gray = filepath + '_gray.png'
        path_gray_full = os.path.join(ROOT, filepath_gray)

        # generate all images and save
        with Image(filepath=path) as img:
            with img.clone() as thumb:
                size = thumb.width if thumb.width < thumb.height else thumb.height
                thumb.crop(width=size, height=size, gravity='center')
                thumb.resize(128, 128)
                thumb.format = "png"
                thumb.save(filepath=path_thumb_full)

            with img.clone() as rotated:
                rotated.rotate(135)
                rotated.format = "png"
                rotated.save(filepath=path_rotated_full)

            with img.clone() as flopped:
                flopped.flop()
                flopped.format = "png"
                flopped.save(filepath=path_flopped_full)

            with img.clone() as gray:
                gray.type = 'grayscale'
                gray.format = "png"
                gray.save(filepath=path_gray_full)

    cnx.commit()
    msg = 'Upload completed!'

    return render_template("script.html",title="uploadForm",
                msg=msg,username=username,password=password)
