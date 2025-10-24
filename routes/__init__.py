from flask import Blueprint

from .superadmin import superadmin_bp
from .admin import admin_bp
from .funcionarios import funcionarios_bp
from .avisos import avisos_bp

__all__ = ["admin_bp", "funcionarios_bp", "superadmin_bp", "avisos_bp"]