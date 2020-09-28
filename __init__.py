from flask import Blueprint

bp = Blueprint('live-assessment', __name__, template_folder = 'templates')

from . import routes, forms, models