from flask import Flask

app = Flask(__name__)

from app import main
from app import s3