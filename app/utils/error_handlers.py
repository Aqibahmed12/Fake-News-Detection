"""
Centralised error handlers for the Flask application.
"""
from flask import jsonify, render_template, request


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(e):
        if _wants_json():
            return jsonify({"error": "Bad Request", "message": str(e)}), 400
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(401)
    def unauthorized(e):
        if _wants_json():
            return jsonify({"error": "Unauthorized", "message": str(e)}), 401
        return render_template("errors/401.html", error=e), 401

    @app.errorhandler(403)
    def forbidden(e):
        if _wants_json():
            return jsonify({"error": "Forbidden", "message": str(e)}), 403
        return render_template("errors/403.html", error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({"error": "Not Found", "message": str(e)}), 404
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        if _wants_json():
            return jsonify({"error": "Rate limit exceeded", "message": str(e)}), 429
        return render_template("errors/429.html", error=e), 429

    @app.errorhandler(500)
    def internal_error(e):
        if _wants_json():
            return jsonify({"error": "Internal Server Error", "message": str(e)}), 500
        return render_template("errors/500.html", error=e), 500


def _wants_json() -> bool:
    return (
        request.path.startswith("/api/")
        or request.accept_mimetypes.best == "application/json"
    )
