# API blueprint package
from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api import detect, results, auth  # noqa: F401, E402
