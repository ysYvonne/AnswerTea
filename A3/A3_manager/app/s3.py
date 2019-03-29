from flask import render_template, redirect,url_for,request
from app import app

import boto3

@app.route('/s3/<id>', methods=['GET'])
#Display details abut a specific bucket
def s3_view(id):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(id)
    keys = bucket.objects.all()
    return render_template("s3view.html",id=id,keys=keys)

