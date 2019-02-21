Face Detection Web Application
===============================

A1 Description
===============
This is web application that can upload pictures, store and detect faces from the uploaded pictures.

Prerequisites
===============
*Python3.7
*flask
*Opencv
*AWS EC2 instance
*MySQL server
*MySQL Python connector
*Credentials to get access to EC2 instance

Perform the following steps to run the web application
=======================================================
Get onto EC2 instance and start web application
1. copy credential (.pem file) to home directory
2. start EC2 instance on aws
3. creat tunnul and connect to cloud: ssh -i credential.pem ubuntu@IPV4_address -L 5901:localhost:5901
4. open VCN by create new connection to localhost:5901, and password is ece1779pass
5. Start mysql-workbench from terminal, connect to the database server, and run 1779a1.sql to create database
5. open terminal and type sh start.sh to start the web application

To use the web application
6. Sign up or log in the account
7. Upload pictures to Portfolio Home
8. Double click the thumb_nailed picture to see face detections
9. Use Auto register button and Auto upload button to automatically create an account and upload pictures! 
10. Have FUN! 
