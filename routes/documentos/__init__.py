import os
from flask import Blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

documentos_bp = Blueprint("documentos", __name__, url_prefix="/documentos", template_folder=os.path.join(BASE_DIR,"templates/documentos"))

from . import documentos