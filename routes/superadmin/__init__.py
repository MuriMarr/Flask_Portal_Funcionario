import os
from flask import Blueprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/superadmin", template_folder=os.path.join(BASE_DIR, "superadmin"), static_folder=os.path.join(BASE_DIR, "static"))

from routes.superadmin import dashboard, empresas, admins