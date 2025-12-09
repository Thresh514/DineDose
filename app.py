from flask import Flask
from extensions import mail, oauth
from pagelogic import test_bp
from pagelogic.login import login_bp
from pagelogic.bp import doctor_page_bp
from pagelogic.repo import drug_repo
from pagelogic.repo import food_repo
from apscheduler.schedulers.background import BackgroundScheduler
from pagelogic.service.notify_service import notify_jobs

notify_interval = 5*60
def notify_cronjob():
    print("Starting notification cron job...")
    notify_jobs(days=1, interval=notify_interval)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    # Initialize extensions
    mail.init_app(app)
    oauth.init_app(app)
    # Register OAuth Provider
    import config
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        api_base_url='https://www.googleapis.com/oauth2/v3/',
        client_id=config.OAUTH_CREDENTIALS['google']['client_id'],
        client_secret=config.OAUTH_CREDENTIALS['google']['client_secret'],
        client_kwargs={'scope': 'openid email profile'}
    )

    # Register Blueprints
    from pagelogic.index import index_bp
    from pagelogic.login import login_bp
    from pagelogic.logout import logout_bp
    from pagelogic.patient_home import patient_home_bp
    from pagelogic.test_bp import test_bp
    from pagelogic.bp import drug_bp, food_bp, plan_bp, user_bp, drug_record_bp, food_record_bp, user_notification_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(patient_home_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(user_bp.user_bp)
    app.register_blueprint(plan_bp.plan_bp)
    app.register_blueprint(food_bp.food_bp)
    app.register_blueprint(drug_bp.drug_bp)
    app.register_blueprint(doctor_page_bp.doctor_page_bp)
    app.register_blueprint(drug_record_bp.drug_record_bp)
    app.register_blueprint(food_record_bp.food_record_bp)
    app.register_blueprint(user_notification_bp.user_notification_bp)

    # Warm up DB caches
    drug_repo.get_drugs()
    drug_repo.drugs
    food_repo.get_foods()
    food_repo.foods

    # Start notification scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(notify_cronjob,'interval', seconds=notify_interval)
    scheduler.start()


    return app


app = create_app()