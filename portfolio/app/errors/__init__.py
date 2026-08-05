from flask import Blueprint

bp = Blueprint('errors', __name__)

# En bas pour éviter les dépendances circulaires...
from app.errors import handlers