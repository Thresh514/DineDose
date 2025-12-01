from flask import Blueprint, request, jsonify, session
from pagelogic.repo import user_notification_repo, user_repo

user_notification_bp = Blueprint("user_notification", __name__)

@user_notification_bp.route('/get_notification_setting', methods=['GET'])
def get_notification_setting_handler():
    """
    给定 user_id，返回这个 user 的通知配置。
    如果找不到，返回 404。
    """
    user_id = int(request.args.get("id"))

    cfg = user_notification_repo.get_notification_config(user_id)
    if cfg is None:
        return jsonify({"error": "notification_config_not_found"}), 404

    return jsonify(cfg.to_dict()), 200

@user_notification_bp.route('/update_notification_setting', methods=['POST'])
def update_notification_setting_handler():
    """
    给定 user_id and new settings, update the notification config.
    if not found, create a new one. 
    """
    data = request.get_json() or {}

    user_id = int(data.get("user_id"))
    enabled = data.get("enabled", True)
    email_enabled = data.get("email_enabled", True)
    notify_minutes = data.get("notify_minutes", [60, 0, -60])
    timezone = data.get("timezone", "UTC")

    if not user_id:
        return jsonify({"error": "missing_user_id"}), 400

    cfg = user_notification_repo.get_notification_config(user_id)
    if not cfg :
        cfg = user_notification_repo.create_notification_config(
            user_id=user_id,
            enabled=enabled,
            email_enabled=email_enabled,
            notify_minutes=notify_minutes,
            timezone=timezone,
        )
        return jsonify(cfg.to_dict()), 200

    cfg.enabled = enabled
    cfg.email_enabled = email_enabled
    cfg.notify_minutes = notify_minutes
    cfg.timezone = timezone

    user_notification_repo.update_notification_config(cfg)

    return jsonify(cfg.to_dict()), 200