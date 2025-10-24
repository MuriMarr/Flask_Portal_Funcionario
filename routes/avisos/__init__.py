import os
from flask import Blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

avisos_bp = Blueprint("avisos", __name__, url_prefix="/avisos", template_folder=os.path.join(BASE_DIR,"templates/avisos"), static_folder=os.path.join(BASE_DIR,"/static"))

from . import avisos_modulo