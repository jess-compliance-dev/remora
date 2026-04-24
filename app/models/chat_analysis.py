from datetime import datetime
from app.extensions.db import db


class ChatAnalysis(db.Model):
    __tablename__ = "chat_analysis"

    analysis_id = db.Column(db.Integer, primary_key=True)

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("memorial_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    current_topic = db.Column(db.String(50), nullable=True)
    topic_complete = db.Column(db.Boolean, nullable=False, default=False)
    show_topic_choices = db.Column(db.Boolean, nullable=False, default=False)
    suggested_topics = db.Column(db.JSON, nullable=True)

    # ✅ NEU
    topic_summary = db.Column(db.Text, nullable=True)
    facts_count = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    session = db.relationship("ChatSession", backref="analysis_entries", lazy=True)
    profile = db.relationship("MemorialProfile", backref="analysis_entries", lazy=True)

    def __repr__(self):
        return f"<ChatAnalysis {self.analysis_id} session={self.session_id} topic={self.current_topic}>"
