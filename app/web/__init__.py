# Web blueprint package
from flask import Blueprint

web_bp = Blueprint("web", __name__)

from app.web import views, dashboard  # noqa: F401, E402
