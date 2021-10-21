from flask import Flask
import logging

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from app import routes
