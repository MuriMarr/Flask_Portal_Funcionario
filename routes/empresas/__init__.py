import os
from flask import Blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

empresas_bp = Blueprint("empresas", __name__, url_prefix="/empresas", template_folder=os.path.join(BASE_DIR,"templates/empresas"), static_folder=os.path.join(BASE_DIR,"/static"))

from . import empresas_modulo