from flask import render_template, redirect, url_for, request, g
from app import webapp
import time

from datetime import datetime, timedelta

import boto3

from app import config
from app.config import db_config

from datetime import datetime, timedelta
from operator import itemgetter
import mysql.connector

s3_bucketName = 'ece1779a2-yf'
placementGroup_name = 'A2_workerpool'


@webapp.route('/ec2_worker/create', methods=['POST'])
# Start a new EC2 instance
def ec2_create():
    # create connection to ec2
    ec2 = boto3.resource('ec2')

    ec2.create_instances(ImageId=config.ami_id, InstanceType='t2.micro', MinCount=1, MaxCount=1,
                         Monitoring={'Enabled': True},
                         Placement={'AvailabilityZone': 'us-east-1d', 'GroupName': placementGroup_name},
                         SecurityGroups=['launch-wizard-10'],
                         KeyName='ECE1779_WEEK5', TagSpecifications=[
                            {
                                'ResourceType': 'instance',
                                'Tags': [
                                    {
                                        'Key': 'Name',
                                        'Value': 'a2_additional_workers'
                                    },
                                ]
                            }, ])

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_worker/delete/<id>', methods=['POST'])
# Terminate a EC2 instance
def ec2_destroy(id):

    ec2 = boto3.resource('ec2')

    ec2.instances.filter(InstanceIds=[id]).terminate()

    return redirect(url_for('ec2_list'))


@webapp.route('/ec2_worker', methods=['GET'])
# Display an HTML list of all ec2 instances
def ec2_list():

    # create connection to ec2
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(
      Filters=[])
# 'Name': 'placement-group-name', 'Values': [placementGroup_name]
    for instance in instances:

         print(instance.id, instance.image_id, instance.key_name, instance.tags)

    return render_template("workers/list.html", title="EC2 Instances", instances=instances)


@webapp.route('/ec2_worker/<id>', methods=['GET'])
# Display details about a specific instance.
def ec2_view(id):

    # print(id)
    ec2 = boto3.resource('ec2')

    # acquire an EC2 instance
    instance = ec2.Instance(id)

    # Create CloudWatch client
    client = boto3.client('cloudwatch')

    request_client = boto3.client('cloudwatch')

    metric_name = 'CPUUtilization'
    namespace = 'AWS/EC2'
    statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

    # request syntax / get cpu statistics
    cpu = client.get_metric_statistics(
        Period=60,
        StartTime=datetime.utcnow() - timedelta(seconds=61 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=1 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId',
                     'Value': id}]

    )

    # print(cpu)

    requestrate = request_client.get_metric_statistics(
        Namespace = 'AWS/ApplicationELB',
        MetricName = 'RequestCount',
        Dimensions = [
            {
                'Name':'LoadBalancer',
                'Value': 'app/a2elb/bb0c5e83fecfb972'
            }
        ],
        StartTime = datetime.utcnow() - timedelta(seconds=61 * 60),
        EndTime = datetime.utcnow() - timedelta(seconds=1 * 60),
        Period = 60,
        Statistics = ['Sum']
    )

    print("request: " + str(requestrate))
    # num = 0
    # for i in requestrate['Datapoints']:
    #     num = num + i.value()[1]
    # print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' + str(num))
    request_rate = []
    for i in requestrate['Datapoints']:
        sum = i['Sum']
        hour = i['Timestamp'].hour
        minute = i['Timestamp'].minute
        time = hour + minute/60
        request_rate.append([time,sum])



    # gather return statistics
    cpu_stats = []

    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        # print(hour)
        minute = point['Timestamp'].minute
        # print(minute)
        time = hour + minute/60
        # print(time)
        # print(point)
        cpu_stats.append([time, point['Average']])

    # print(cpu_stats)

    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    # print(cpu_stats)

    return render_template("workers/view.html", title="Instance Info",
                           instance=instance,
                           cpu_stats=cpu_stats,
                           request_rate = request_rate)


# connect the database
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


@webapp.route('/s3/delete', methods=['POST'])
# delete all files in s3 bucket and the data in RDS
def delete():

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("""SET FOREIGN_KEY_CHECKS = 0""")
    cnx.commit()

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("""TRUNCATE table photo""")
    cnx.commit()

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("""TRUNCATE table user""")
    cnx.commit()

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("""SET FOREIGN_KEY_CHECKS = 1""")
    cnx.commit()

    cnx = get_db()
    cursor = cnx.cursor()
    cursor.execute("""TRUNCATE table storedphoto""")
    cnx.commit()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(s3_bucketName)

    keys = bucket.objects.all()

    for k in keys:
        image_name = k.key
        print(image_name)
        s3.Object(s3_bucketName, image_name).delete()

    return redirect(url_for('s3_list'))




@webapp.route('/manage_worker_pool', methods=['POST'])
def manage_worker_pool():
# while True:
    increase_rate = float(request.form.get('grow_rate'))
    print(increase_rate)

    min_threshold = float(request.form.get('min_threshold'))
    print(min_threshold)

    decrease_rate = float(request.form.get('shrink_rate'))
    print(decrease_rate)

    max_threshold = float(request.form.get('max_threshold'))
    print(max_threshold)


    # create connection to ec2
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(
      Filters=[

          {'Name': 'instance-state-name',
           'Values': ['running']
           },
      ]
    )

    #instances = ec2.instances.all()
    cpu_stats_1 = []
    ids = []

    for instance in instances:

        ids.append(instance.id)

        client = boto3.client('cloudwatch')

        # get cpu statistics in 1 minute(60s)

        cpu_1 = client.get_metric_statistics(
            Period=60,
            StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=1 * 60),
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',  # Unit='Percent',
            Statistics=['Average'],
            Dimensions=[{'Name': 'InstanceId',
                         'Value': instance.id}]
        )

        # gather return statistics

        for point in cpu_1['Datapoints']:

            load = round(point['Average'], 2)
            cpu_stats_1.append(load)

    average_load = sum(cpu_stats_1) / len(cpu_stats_1)

    # print(cpu_stats_1)
    # print(average_load)
    # print(ids)

# option 1
    if average_load > max_threshold:
        # the number of new ec2 instances
        add_instance_num = int(len(cpu_stats_1) * (increase_rate-1)+1)
        print("add_instance_num: " + str(add_instance_num))

        # add instances
        for i in range(add_instance_num) :
            instances = ec2.create_instances(ImageId=config.ami_id, InstanceType='t2.micro', MinCount=1, MaxCount=1,
                         Monitoring={'Enabled': True},
                         Placement={'AvailabilityZone': 'us-east-1d'},
                         SecurityGroups=['launch-wizard-10'],
                         KeyName='ECE1779_WEEK5', TagSpecifications=[
                            {
                                'ResourceType': 'instance',
                                'Tags': [
                                    {
                                        'Key': 'Name',
                                        'Value': 'a2_additional_workers'
                                    },
                                ]
                            }, ])


        # resize ELB
        for instance in instances:
            # print(instance.id)
            ec2 = boto3.resource('ec2')
            instance.wait_until_running(
                Filters=[
                    {
                        'Name': 'instance-id',
                        'Values': [
                            instance.id,
                        ]
                    },
                ],
            )

            # print(instance.id)
            client = boto3.client('elbv2')
            client.register_targets(
                TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:359874305462:targetgroup/a2target/7429bd06a429315e',
                Targets=[
                    {
                        'Id': instance.id,
                    },
                ]
            )


            # wait until finish
            waiter = client.get_waiter('target_in_service')
            waiter.wait(
                TargetGroupArn= 'arn:aws:elasticloadbalancing:us-east-1:359874305462:targetgroup/a2target/7429bd06a429315e',
                Targets=[
                    {
                        'Id': instance.id,
                    },
                ],
            )


# option 2
    if average_load < min_threshold:
        minus_instance_num = int(len(cpu_stats_1) * (1-decrease_rate))
        print("minus_instance_num: " + str(minus_instance_num))

        if minus_instance_num > 0:
            ids_to_delete = ids[:minus_instance_num]
            #             # print(ids_to_delete)

            #resize ELB
            for id in ids_to_delete:
                # print(id)
                client = boto3.client('elbv2')
                client.deregister_targets(
                    TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:359874305462:targetgroup/a2target/7429bd06a429315e',
                    Targets=[
                        {
                            'Id': id,
                        },
                    ]
                )

                # wait until finish
                waiter = client.get_waiter('target_deregistered')
                waiter.wait(
                    TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:359874305462:targetgroup/a2target/7429bd06a429315e',
                    Targets=[
                        {
                            'Id': id,
                        },
                    ],

                )

            # drop instances
            for id in ids_to_delete:
                # print(id)
                ec2.instances.filter(InstanceIds=[id]).terminate()

    # wait for 1 minute
    time.sleep(60)
    return 'ok'
