import uuid
from datetime import datetime, timezone
from app.extensions import db


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey("api_keys.id"), nullable=True)

    # Input
    input_text = db.Column(db.Text, nullable=True)
    input_url = db.Column(db.String(2048), nullable=True)
    source_type = db.Column(db.String(16), default="text")  # text | url | file

    # Result
    score = db.Column(db.Float, nullable=True)          # 0.0 – 1.0
    label = db.Column(db.String(16), nullable=True)     # REAL | LIKELY_REAL | ...
    confidence = db.Column(db.Float, nullable=True)
    features_json = db.Column(db.Text, nullable=True)   # JSON string
    model_used = db.Column(db.String(32), default="logistic")
    processing_ms = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self, include_text=False):
        d = {
            "result_id": self.id,
            "score": self.score,
            "label": self.label,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "processing_ms": self.processing_ms,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "source_type": self.source_type,
        }
        if include_text:
            d["input_text"] = self.input_text
            d["input_url"] = self.input_url
        return d

    def __repr__(self):
        return f"<Submission {self.id} label={self.label}>"
