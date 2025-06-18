# ── main.py (or whichever file you use to start the app) ──

from config import app, db
from model_editor import model_editor_bp
from model_converter import model_converter_bp
from surrogate_model import surrogate_modeling_bp
from simulations import simulations_bp

# Register each blueprint under its URL prefix
app.register_blueprint(model_editor_bp, url_prefix='/model_editor')
app.register_blueprint(model_converter_bp, url_prefix='/model_converter')
app.register_blueprint(surrogate_modeling_bp, url_prefix='/surrogate_modeling')
app.register_blueprint(simulations_bp, url_prefix='/simulations')

if __name__ == '__main__':
    # Create all database tables if they don't already exist
    with app.app_context():
        db.create_all()

    # Run the Flask development server:
    # - host="0.0.0.0" makes the app listen on all interfaces inside the container,
    #   allowing Docker to forward port 5000 from the host into this container.
    # - port=5000 ensures the container’s Flask matches your docker-compose “5000:5000” mapping.
    # - debug=True keeps the built-in debugger and auto-reloader active (development mode).
    app.run(host="0.0.0.0", port=5000, debug=True)
