import secrets
import hashlib
from datetime import datetime, timezone
from app.extensions import db


class APIKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(64), nullable=False, default="My API Key")
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    prefix = db.Column(db.String(8), nullable=False)    # First 8 chars for display
    rate_limit = db.Column(db.Integer, default=60)      # requests per minute
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = db.Column(db.DateTime, nullable=True)

    submissions = db.relationship("Submission", backref="api_key", lazy="dynamic")

    @staticmethod
    def generate() -> tuple[str, "APIKey"]:
        """Generate a new API key. Returns (plain_key, APIKey_instance)."""
        raw = "fnd_" + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        instance = APIKey(key_hash=key_hash, prefix=raw[:8])
        return raw, instance

    @staticmethod
    def verify(raw_key: str) -> "APIKey | None":
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return APIKey.query.filter_by(key_hash=key_hash, is_active=True).first()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix + "****",
            "rate_limit": self.rate_limit,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    def __repr__(self):
        return f"<APIKey {self.prefix}...>"
