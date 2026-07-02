from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .drills_data import get_drills
from .extensions import db
from .models import Match, MatchEvent, StatEntry
from .services.analytics import PerformanceAnalyzer
from .services.football_data import get_fixtures, get_league_by_id, get_leagues, get_results, get_table
from .services.football_news import get_headlines, get_transfer_news

main_bp = Blueprint("main", __name__)

HEALTH_FIELDS = ["matches", "distance", "minutes", "challenges", "goals", "assists", "injuries"]
HEALTH_FLOAT_FIELDS = {"distance"}

MATCH_EVENT_TYPES = {"goal", "card", "sub", "note"}


def _active_match():
    return Match.query.filter_by(user_id=current_user.id, ended_at=None).first()


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    stats = current_user.stats
    latest = stats[-1] if stats else None
    analysis = PerformanceAnalyzer(stats).analyze()
    ai_messages = [{"text": review} for review in analysis["reviews"]] or [{"text": analysis["advice"]}]
    history = list(reversed(stats))[:10]

    return render_template(
        "dashboard.html",
        username=current_user.username,
        latest=latest,
        history=history,
        performance_score=analysis["score"],
        ai_reviews=analysis["reviews"],
        ai_messages=ai_messages,
        performance_level=analysis["level"],
        suggestion_text=analysis["suggestion"],
        training_advice=analysis["advice"],
        user_level=current_user.level,
        user_xp=current_user.xp,
        streak=current_user.streak,
    )


@main_bp.route("/health", methods=["GET", "POST"])
@login_required
def health():
    if request.method == "POST":
        try:
            values = {
                field: float(request.form[field]) if field in HEALTH_FLOAT_FIELDS else int(request.form[field])
                for field in HEALTH_FIELDS
            }
        except (KeyError, ValueError):
            flash("Please enter valid numbers for every field.")
            return render_template("health.html")

        db.session.add(StatEntry(user_id=current_user.id, timestamp=datetime.utcnow(), **values))
        db.session.commit()
        return redirect(url_for("main.dashboard"))
    return render_template("health.html")


@main_bp.route("/news")
@login_required
def news():
    return render_template("news.html", headlines=get_headlines(), transfers=get_transfer_news())


@main_bp.route("/leagues")
@login_required
def leagues():
    return render_template("leagues.html", leagues=get_leagues())


@main_bp.route("/leagues/<league_id>")
@login_required
def league_detail(league_id):
    league = get_league_by_id(league_id)
    if league is None:
        flash("Unknown league.")
        return redirect(url_for("main.leagues"))

    return render_template(
        "league_detail.html",
        league=league,
        table=get_table(league_id),
        fixtures=get_fixtures(league_id),
        results=get_results(league_id),
    )


@main_bp.route("/drills")
@login_required
def drills():
    return render_template("drills.html", drills=get_drills())


@main_bp.route("/live", methods=["GET", "POST"])
@login_required
def live():
    if request.method == "POST":
        if _active_match() is None:
            db.session.add(
                Match(user_id=current_user.id, opponent=request.form.get("opponent", "").strip() or None)
            )
            db.session.commit()
        return redirect(url_for("main.live"))

    return render_template("live.html", match=_active_match())


@main_bp.route("/live/event", methods=["POST"])
@login_required
def live_event():
    match = _active_match()
    if match is None:
        return jsonify({"error": "No active match."}), 400

    event_type = request.form.get("event_type")
    if event_type not in MATCH_EVENT_TYPES:
        return jsonify({"error": "Invalid event type."}), 400

    elapsed_minutes = int((datetime.utcnow() - match.started_at).total_seconds() // 60)
    db.session.add(
        MatchEvent(
            match_id=match.id,
            event_type=event_type,
            minute=elapsed_minutes,
            note=request.form.get("note", "").strip() or None,
        )
    )
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/live/events")
@login_required
def live_events():
    match = _active_match()
    if match is None:
        return jsonify({"active": False, "events": []})

    return jsonify(
        {
            "active": True,
            "opponent": match.opponent,
            "started_at": match.started_at.isoformat() + "Z",
            "events": [
                {"type": e.event_type, "minute": e.minute, "note": e.note}
                for e in match.events
            ],
        }
    )


@main_bp.route("/live/end", methods=["POST"])
@login_required
def live_end():
    match = _active_match()
    if match is not None:
        match.ended_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for("main.live"))


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", "").strip() or current_user.name
        current_user.position = request.form.get("position", "").strip() or current_user.position
        age = request.form.get("age", "")
        if age:
            try:
                current_user.age = int(age)
            except ValueError:
                flash("Age must be a number.")
        db.session.commit()

    return render_template(
        "profile.html",
        user={"profile": {"name": current_user.name, "age": current_user.age, "position": current_user.position}},
        user_level=current_user.level,
        user_xp=current_user.xp,
    )
