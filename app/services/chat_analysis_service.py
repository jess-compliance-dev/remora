from app.extensions.db import db
from app.models.chat_analysis import ChatAnalysis


class ChatAnalysisService:
    def create_analysis(self, data: dict):
        analysis = ChatAnalysis(
            session_id=data.get("session_id"),
            profile_id=data.get("profile_id"),
            current_topic=data.get("current_topic"),
            topic_complete=bool(data.get("topic_complete", False)),
            show_topic_choices=bool(data.get("show_topic_choices", False)),
            suggested_topics=data.get("suggested_topics") or [],
        )

        db.session.add(analysis)
        db.session.commit()
        return analysis

    def get_latest_by_session_id(self, session_id: int):
        return (
            ChatAnalysis.query
            .filter_by(session_id=session_id)
            .order_by(ChatAnalysis.created_at.desc(), ChatAnalysis.analysis_id.desc())
            .first()
        )

    def get_all_by_session_id(self, session_id: int):
        return (
            ChatAnalysis.query
            .filter_by(session_id=session_id)
            .order_by(ChatAnalysis.created_at.asc(), ChatAnalysis.analysis_id.asc())
            .all()
        )
