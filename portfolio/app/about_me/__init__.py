from flask import Blueprint

bp = Blueprint('about_me', __name__)

from app.about_me import routes