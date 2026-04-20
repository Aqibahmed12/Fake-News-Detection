"""Entry point for the Fake News Detection Platform."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Auto-train model if not present
    from app.services.ml_engine import MLEngine
    engine = MLEngine(app.config["MODELS_DIR"])
    if not engine.is_trained():
        print("[Startup] No trained model found — training now (this may take ~30s)...")
        from train_model import train_and_save
        train_and_save(app.config["MODELS_DIR"], app.config["DATA_DIR"])
        print("[Startup] Model training complete.")

    app.run(debug=True, host="0.0.0.0", port=5000)
