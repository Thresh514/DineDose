from flask import Blueprint, render_template, request, jsonify, session
from pagelogic.repo import user_notification_repo

user_notification_bp = Blueprint("user_notification", __name__)

@user_notification_bp.route("/notification_setting_page", methods=["GET"])
def notification_settings_page():
    """
    Render the Notification Settings page for the current logged-in user.
    user_id is taken from session.
    """
    user_id = session.get("user_id")
    if not user_id:
        # you can redirect to login if you have auth
        # return redirect(url_for("auth.login"))
        return "Not logged in", 401

    return render_template("patient_notification_settings.html")


@user_notification_bp.route('/get_notification_setting', methods=['GET'])
def get_notification_setting_handler():
    """Get notification settings by user_id."""
    user_id = int(request.args.get("id"))

    cfg = user_notification_repo.get_notification_config(user_id)
    if cfg is None:
        return jsonify({"error": "notification_config_not_found"}), 404

    return jsonify(cfg.to_dict()), 200

@user_notification_bp.route('/update_notification_setting', methods=['POST'])
def update_notification_setting_handler():
    """Update notification config by user_id. Create new one if not found."""
    data = request.get_json() or {}

    user_id = int(data.get("user_id"))
    enabled = data.get("enabled", True)
    email_enabled = data.get("email_enabled", True)
    notify_minutes = data.get("notify_minutes", [60, 0, -60])
    timezone = data.get("timezone", "UTC")

    if not user_id:
        return jsonify({"error": "missing_user_id"}), 400

    cfg = user_notification_repo.get_notification_config(user_id)
    if not cfg:
        new_cfg = user_notification_repo.NotificationConfig(
            user_id=user_id,
            enabled=enabled,
            email_enabled=email_enabled,
            notify_minutes=notify_minutes,
            timezone=timezone,
        )
        user_notification_repo.create_notification_config(new_cfg)
        cfg = new_cfg
    else:
        cfg.enabled = enabled
        cfg.email_enabled = email_enabled
        cfg.notify_minutes = notify_minutes
        cfg.timezone = timezone
        user_notification_repo.update_notification_config(cfg)
    
    return jsonify({"status": "success"}), 200