from flask import render_template, redirect, url_for, request,flash
from app import app
import boto3
from app import dynamo
import smtplib
from app import s3_config
from werkzeug.utils import secure_filename

a3BucketName = 'ece1779a3itemsbucket'

ALLOWED_EXTENSIONS = set(['jpg', 'png', 'gif'])
app.secret_key = '\x86j\x94\xab\x15\xedy\xe4\x1f\x0b\xe9\xb9v}C\xb9\xf1\xech\x0bs.\x10$'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
# display an HTML list of all instances
def dashboard():
    # create connection to s3
    s3 = boto3.resource('s3')
    buckets = s3.buckets.all()
    orders = dynamo.orders_getall()
    return render_template("Dashboard.html",orders = orders , buckets=buckets)

@app.route('/add_product')
def add_product():
    categories = dynamo.categories_list_all()
    return render_template('add.html', categories=categories)

@app.route('/remove_product')
def remove_product():
    data = dynamo.products_list_all()
    return render_template("remove.html", data=data)


@app.route('/addItem', methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        productName = request.form['name']
        price = request.form['price']
        description = request.form['description']
        stock = request.form['stock']
        categoryId = int(request.form['category'])

        if productName == '' or price == '' or description == '' or stock == '' or not stock.isdigit():
            flash("Please fill in all the fields")
            return redirect(url_for('add_product'))

        # Uploading image
        image = request.files['image']
        productId = dynamo.max_productID() + 1
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            if filename == '':
                flash("Please upload an image")
                return redirect(url_for('add_product'))

            #save the uploaded file to s3 bucket
            s3 = s3_config.create_connection()
            if not s3_config.validate_bucket_exists(s3, a3BucketName):
                s3_config.create_bucket(s3,a3BucketName)

            s3_config.store_data(s3,a3BucketName,'products/'+str(productId)+"_"+filename, image)

        else:
            flash("Please upload an image")
            return redirect(url_for('add_product'))

        imagename = str(productId)+"_"+filename
        flash("New product has been successfully added")
        dynamo.products_put(productId,productName,str(float(price)),description,imagename,int(stock),categoryId)
        return redirect(url_for('add_product'))


@app.route("/removeItem")
def removeItem():
    productId = request.args.get('productId')
    # DELETE FROM products WHERE productID = ' + productId
    dynamo.products_delete_productId(int(productId))
    return redirect(url_for('remove_product'))


@app.route('/products_restock')
def products_restock():
    itemData = dynamo.products_list_all()
    return render_template('restock.html', itemData=itemData)

@app.route('/stock_update/<id>', methods=['POST'])
def stock_update(id):
    productId = int(id)
    new_amount = request.form['restock'+id]
    if new_amount == '' or not new_amount.isdigit():
        return redirect(url_for('products_restock'))
    dynamo.restock_update(id,new_amount)
    return redirect(url_for('products_restock'))

@app.route('/complete_order/<userId>/<orderId>',methods=['POST'])
def complete_order(userId,orderId):
    dynamo.orders_update(int(userId),int(orderId))
   # email = dynamo.users_getemail(int(userId))[0]
   # sendemail(from_addr='letteropener2011@gmail.com',
    #          to_addr_list=[email],
     #        cc_addr_list=[],
      #       subject='Your order has completed',
       #       message='Your order ' + orderId + ' has completed',
        #      login='AKIAIDF4JC7SE2SNZIEQ',
         #     password='AsKNTl3PffDBBgUu1xKjXecea86gfCI7xt1sKkqEHWOQ')
    return redirect(url_for('dashboard'))


def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='email-smtp.us-east-1.amazonaws.com:587'):
    client = boto3.client('ses')
    response = client.list_verified_email_addresses()
    if to_addr_list[0] in response['VerifiedEmailAddresses']:
        header = 'From: %s\n' % from_addr
        header += 'To: %s\n' % ','.join(to_addr_list)
        header += 'Cc: %s\n' % ','.join(cc_addr_list)
        header += 'Subject: %s\n\n' % subject
        message = header + message
        server = smtplib.SMTP(smtpserver)
        server.ehlo()
        server.starttls()
        server.login(login, password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        server.quit()
        return problems
    else:
        client.verify_email_identity(
            EmailAddress=to_addr_list[0]
        )
        return "wait user email verification"

