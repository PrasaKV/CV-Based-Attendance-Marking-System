import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    g
)

web_bp = Blueprint("web", __name__)

def get_db():
    if "db" not in g:
        from app.models.database import DatabaseManager
        g.db = DatabaseManager(current_app.config["DATABASE"])
    return g.db


@web_bp.route("/")
def index():
    """Main Upload Dashboard"""
    db = get_db()
    recent_sessions = db.get_all_sessions(limit=5)
    return render_template("index.html", recent_sessions=recent_sessions)


@web_bp.route("/results/<session_id_or_key>")
def results(session_id_or_key):
    """Session Details & Attendance Interactive Results View"""
    db = get_db()
    session = db.get_session(session_id_or_key)
    if not session:
        flash("Session not found.", "danger")
        return redirect(url_for("web.index"))

    records = db.get_session_records(session["id"])
    return render_template("results.html", session=session, records=records)


@web_bp.route("/history")
def history():
    """Session History Archive View"""
    db = get_db()
    sessions = db.get_all_sessions(limit=100)
    return render_template("history.html", sessions=sessions)


@web_bp.route("/analytics")
def analytics():
    """Visual Analytics View"""
    db = get_db()
    summary = db.get_analytics_summary()
    return render_template("analytics.html", summary=summary)
