import os
from flask import Blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder=os.path.join(BASE_DIR,"templates/admin"), static_folder=os.path.join(BASE_DIR,"/static"))

from . import dashboard, ferias, funcionarios, ponto