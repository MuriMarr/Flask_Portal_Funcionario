import os
from flask import Blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

funcionarios_bp = Blueprint("funcionarios", __name__, url_prefix="/funcionarios", template_folder=os.path.join(BASE_DIR, "funcionarios"), static_folder=os.path.join(BASE_DIR, "static"))

from routes.funcionarios import dashboard, ferias, ponto, banco_horas
from routes.common import pdf_utils