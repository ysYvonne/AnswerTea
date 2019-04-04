from builtins import int

from flask import render_template, session, redirect, request, url_for, flash, jsonify
import hashlib
from app import app
from app import dynamo
from app import s3_config
from passlib.hash import pbkdf2_sha256

a3BucketName = 'ece1779a3itemsbucket'

# set secret key for session
app.secret_key = '\x86j\x94\xab\x15\xedy\xe4\x1f\x0b\xe9\xb9v}C\xb9\xf1\xech\x0bs.\x10$'
ALLOWED_EXTENSIONS = set(['jpg', 'png', 'gif','JPG'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def getLoginDetails():
    if ('email' not in session) or not dynamo.check_table_availability('users') or \
            not dynamo.check_table_availability('categories') or not dynamo.check_table_availability('products') \
            or not dynamo.check_table_availability('kart'):
        loggedIn = False
        firstName = ''
        noOfItems = 0
        userId = 0
    else:
        loggedIn = True
        record=dynamo.users_email_userId(session['email'])
        if len(record) != 0:
            userId = record[0][1]
            record=dynamo.users_email_firstName(session['email'])
            firstName = record[0][1]
            record=dynamo.kart_userId_productId(userId)
            noOfItems = 0
            i = 0
            while i < len(record):
                noOfItems = noOfItems + record[i]['amount']
                i = i + 1
        else:
            session.pop("email", None)
            loggedIn = False
            firstName = ''
            noOfItems = 0
            userId = 0
    return (loggedIn, firstName,noOfItems,userId)

@app.route("/")
def root():
    # get login user info
    loggedIn, firstName, noOfItems,userId = getLoginDetails()
    # get all products info
    itemData=dynamo.products_list_all()
    # get all category info
    categoryData=dynamo.categories_list_all()

    print(itemData)

    return render_template('home.html',
                           itemdata=itemData,
                           loggedIn=loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems,
                           categoryData=categoryData)

@app.route("/search", methods = ["POST"])
def search():
    if request.method == "POST":
        loggedIn, firstName, noOfItems, userId = getLoginDetails()
        itemData = dynamo.products_list_all()
        categoryData = dynamo.categories_list_all()
        searchkeyword = request.form['search']
        result = []
        for item in itemData:
            for row in item:
                if searchkeyword in row[1]:
                    result.append([row])
        return render_template('home.html', itemData=result, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,
                               categoryData=categoryData)

@app.route("/submit_order",methods = ["POST"])
def submit_order():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    kart = dynamo.kart_get(userId)
    totalPrice = 0
    if len(kart) != 0:
        msg = ""
        i = 0
        order_description = ""
        while i < len(kart):
            stock_status = dynamo.stock_update(kart[i][1], kart[i][2])
            if stock_status[0] == 0:
                order_description = order_description + str(kart[i][3]) + " × " + str(kart[i][2]) + " | "
                totalPrice = totalPrice + float(kart[i][6])
            elif stock_status[0] == -1:
                msg = stock_status[1]
                for item in kart:
                    dynamo.kart_removeAll(userId, int(item[1]))
                kart = dynamo.kart_get(userId)
                loggedIn, firstName, noOfItems, userId = getLoginDetails()
                totalPrice = 0
                return render_template("cart.html", msg=msg,
                                       products=kart, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName,
                                       noOfItems=noOfItems)
            else:
                order_description = order_description + str(kart[i][3]) + " × " + str(stock_status[0]) + " | "
                msg = msg + stock_status[1]
                totalPrice = totalPrice + float(int(stock_status[0]) * float(kart[i][5]) )

            i = i + 1
        dynamo.order_put(userId, order_description, str(format(totalPrice,'.2f')), "processing")
        for item in kart:
            dynamo.kart_removeAll(userId,int(item[1]))

        kart = dynamo.kart_get(userId)
        loggedIn, firstName, noOfItems, userId = getLoginDetails()
        totalPrice = 0
        msg = msg + "Your order has been submitted, Thanks for shopping!"
    else:
        msg = "Your cart is empty !"
    return render_template("cart.html",msg = msg,
                           products = kart, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/account/orders")
def viewOrders():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    orders = dynamo.orders_get(userId)
    if len(orders) == 0:
        msg = "No order record"
        return render_template("orders.html",msg = msg, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
    else:
        return render_template("orders.html", orders=orders, loggedIn=loggedIn, firstName=firstName,
                               noOfItems=noOfItems)




@app.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    categoryId = request.args.get("categoryId")
    categoryName = dynamo.get_category_name(int(categoryId))
    data = dynamo.products_in_category(int(categoryId))
    return render_template('displayCategory.html',data=data, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryName=categoryName[0])


@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn,firstName,noOfItems, userId=getLoginDetails()
    return render_template('profileHome.html', loggedIn=loggedIn,firstName=firstName,noOfItems=noOfItems)

@app.route("/account/profile/view")
def viewProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    profileData=dynamo.users_email_all(session['email'])
    return render_template('viewProfile.html',profileData=profileData,loggedIn=loggedIn,firstName=firstName,noOfItems=noOfItems)


@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    profileData=dynamo.users_email_all(session['email'])
    return render_template('editProfile.html',profileData=profileData,loggedIn=loggedIn,firstName=firstName,noOfItems=noOfItems)


@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        data=dynamo.users_email_password(session['email'])
        password = data[0][1]
        data=dynamo.users_email_userId(session['email'])
        userId = data[0][1]
        if (password == oldPassword):
            dynamo.users_update_password_userId(userId,newPassword)
            msg="Changed successfully"
            return render_template("changePassword.html", msg=msg)
        else:
            msg = "Old password does not match system record"
            return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")


@app.route("/updateProfile", methods=["POST"])
def updateProfile():
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    if loggedIn:
        if request.method == 'POST':
            firstName = request.form['firstName']
            lastName = request.form['lastName']
            address1 = request.form['address1']
            address2 = request.form['address2']
            zipcode = request.form['zipcode']
            city = request.form['city']
            province = request.form['province']
            country = request.form['country']
            phone = request.form['phone']

            if (firstName == ''):
                msg = "firstname cannot be empty"
                profileData = dynamo.users_email_all(session['email'])
                return render_template("editProfile.html", error=msg,profileData=profileData,loggedIn=loggedIn,firstName=firstName,noOfItems=noOfItems)
            else:
                userdetail = [lastName, address1, address2, zipcode, city, province, country, phone]

                i = 0
                while i < len(userdetail):
                    if userdetail[i] == '':
                        userdetail[i] = " "
                    i = i + 1
                dynamo.users_update_all_userId(userId, session['email'], firstName, userdetail)
                profileData = dynamo.users_email_all(session['email'])
                msg = "Updated Successfully"
                return render_template("editProfile.html", error=msg,profileData=profileData,loggedIn=loggedIn,firstName=firstName,noOfItems=noOfItems)
    else:
        return redirect(url_for('root'))


@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html',error='')


@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        if is_valid(email,password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            msg = "Invalid email or password"
            return render_template('login.html', error = msg)


@app.route("/productDescription")
def productDescription():
    # get user info
    loggedIn, firstName, noOfItems, userId = getLoginDetails()
    # get id from front end
    productId = request.args.get('productId')
    # get specific product item from dynamodb
    productData=dynamo.products_productId_search(int(productId))
    # get corresponding image from s3 bucket
    imageurl = s3_config.get_element_from_bucket(a3BucketName, productData[0]['image'])
    productData[0]['image'] = imageurl

    # render product detail page
    return render_template("single.html",
                           data=productData,
                           loggedIn=loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/addToCart")
def addToCart():
    # if 'email' not in session:
    #     return redirect(url_for('loginForm'))
    # else:
    #     record = dynamo.users_email_userId(session['email'])
        # static user id for test
        # userId = record[0][1]
        error = ''
        loggedIn, firstName, noOfItems, userId = getLoginDetails()
        userId = 1

        productId = int(request.args.get('productId'))

        # dynamo.kart_put(userId,int(productId),1)


        productData = dynamo.products_productId_search(int(productId))
        current_stock = productData[0]['stock']


        imageurl = s3_config.get_element_from_bucket(a3BucketName, productData[0]['image'])
        productData[0]['image'] = imageurl
        # get corresponding image from s3 bucket
        if current_stock > 0:
            dynamo.kart_put(userId, int(productId), 1)
            # imageurl = s3_config.get_element_from_bucket(a3BucketName, productData[0]['image'])
            # productData[0]['image'] = imageurl
            dynamo.stock_update(productId, 1)
            error='This item has been successfully added to the cart!'

# render product detail page

        else:
            error = 'This product is currently out of stock!'
        return render_template("single.html",
                               error = error,
                               data=productData,
                               loggedIn=loggedIn,
                               firstName=firstName,
                               noOfItems=noOfItems)


@app.route("/cart")
def cart():
    # if 'email' not in session:
    #     return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()

    # static user id for test
    kart = dynamo.kart_get(1)

    totalPrice = 0
    i = 0
    while i < len(kart):
        totalPrice = totalPrice + float(kart[i][6]) * float(kart[i][7])
        i = i + 1

    print(kart)
    return render_template("checkout.html",
                           products = kart,
                           totalPrice = format(totalPrice,'.2f'),
                           loggedIn = loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/removeOneFromCart")
def removeOneFromCart():
    # if 'email' not in session:
    #     return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems, userId = getLoginDetails()

    productId = int(request.args.get('productId'))

    dynamo.kart_removeOne(userId, productId)

    return redirect(url_for('cart'))

@app.route("/removeAllFromCart")
def removeAllFromCart():

    # if 'email' not in session:
    #     return redirect(url_for('loginForm'))

    loggedIn, firstName, noOfItems, userId = getLoginDetails()

    productId = int(request.args.get('productId'))

    dynamo.kart_removeAll(1, productId)
    return redirect(url_for('cart'))

@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("root"))


# def is_valid(email, password):
#     data = dynamo.users_email_password(email)
#     if len(data) != 0:
#         if data[0][0] == email and data[0][1] == hashlib.md5(password.encode()).hexdigest():
#             return True
#         return False
#     return False

def is_valid(email, password):
    if email=='' or password=='':
        return False
    data = dynamo.users_email_password(email)
    if len(data) != 0:
        stored_pw=bytes(data[0][1], 'utf-8')

        # if data[0][0] == email and data[0][1] == hashlib.md5(password.encode()).hexdigest():
        if data[0][0] == email and pbkdf2_sha256.verify(password, stored_pw):
            return True
        return False
    return False


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        province = request.form['province']
        country = request.form['country']
        phone = request.form['phone']

        if (password == '' or email == '' or firstName == ''):
            msg = "email, password , firstname cannot be empty"
            return render_template("register.html", error=msg)
        else:

            userdetail = [lastName,address1,address2,zipcode,city,province,country,phone]
            i = 0
            while i < len(userdetail):
                if userdetail[i] == '':
                    userdetail[i] = " "
                i = i + 1
            check_email = dynamo.users_email_userId(email)
            if len(check_email) == 0:
                hash_salt_pw = pbkdf2_sha256.encrypt((bytes(password, 'utf-8')), salt_size=16)
                dynamo.users_put(hash_salt_pw, email, firstName, userdetail)
                # dynamo.users_put(hashlib.md5(password.encode()).hexdigest(), email, firstName, userdetail)
                msg = "Registered Successfully"
            else:
                msg = "Email already exists, please register with another one"
            return render_template("login.html", error=msg)


@app.route("/registrationForm")
def registrationForm():
    return render_template("register.html")



@app.route("/categories_list")
def categories_list():

    loggedIn, firstName, noOfItems, userId = getLoginDetails()

    category_id = request.args.get('category_id')
    productData = dynamo.products_productId_categoryId(int(category_id))
    # get corresponding image from s3 bucket
    type = 'categories'
    print('main')
    print(productData)
    return render_template("list.html",
                           itemdata=productData,
                           loggedIn=loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems,
                           type = type,
                           category_id=category_id)
@app.route("/youtubers_list")
def youtubers_list():

    loggedIn, firstName, noOfItems, userId = getLoginDetails()

    youtuber_id = request.args.get('youtuber_id')


    productData = dynamo.products_in_youtuber(int(youtuber_id))
    # get corresponding image from s3 bucket
    type = 'youtubers'
    print('main')
    print(productData)
    return render_template("list.html",
                           itemdata=productData,
                           loggedIn=loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems,
                           type = type,
                           youtuber_id=youtuber_id)


# @app.route("/makeup",methods=["POST"])
# def makeup():
#
#     product_id = request.form['productId']
#     image_file = request.files['image']
#     print(image_file)
#
#     imageUrl = process_face(product_id, image_file)
#
#     return jsonify(imageUrl)
#
# def process_face(product_id, image_file):
#
#     productData = dynamo.products_productId_search(int(product_id))
#     categoryId = productData[0]['categoryId']
#     rgb = productData[0]['RGB']
#     # categoryId, rgb = dynamo.get_categoryId_from_productId(product_id)
#     RGB = rgb.split('/')
#
#     filename = secure_filename(image_file.filename)
#
#     if image_file and allowed_file(image_file.filename):
#         filename = secure_filename(image_file.filename)
#         if filename == '':
#             flash("Please upload an image")
#
#         # Get the service client and upload to the s3 bucket
#         file_key_name = 'facePic/' + filename
#         s3 = s3_config.create_connection()
#         s3_config.store_data(s3, a3BucketName, file_key_name, image_file)
#
#     else:
#         flash("Please upload an image")
#
#     # get the url of the upload image
#     imageUrl = s3_config.get_face_from_bucket(a3BucketName, filename)
#
#     AM = ApplyMakeup()
#
#     if categoryId == 1:
#         output_img_stream = AM.apply_lipstick(imageUrl, int(RGB[0]), int(RGB[1]), int(RGB[2]))  # (R,G,B) - (170,10,30)
#     elif categoryId == 2:
#         output_img_stream = AM.apply_blush(imageUrl, int(RGB[0]), int(RGB[1]), int(RGB[2]))  # (R,G,B) - (170,10,30)
#
#
#     # upload after pic to s3
#     fn = filename.split('.')
#     filename_lip = fn[0] + "_lip.jpg"
#     filename_lip_key_name = 'facePic/' + filename_lip
#     s3 = s3_config.create_connection()
#     s3_config.store_data(s3, a3BucketName, filename_lip_key_name, output_img_stream)
#
#     imageUrl_lip = s3_config.get_face_from_bucket(a3BucketName, filename_lip)
#
#     return imageUrl_lip