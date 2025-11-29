from flask import Flask
from extensions import mail, oauth
from pagelogic import test_bp
from pagelogic.login import login_bp
from pagelogic.bp import doctor_page_bp
from pagelogic.repo import drug_repo
from pagelogic.repo import food_repo
from pagelogic.bp import drug_record_bp
from apscheduler.schedulers.background import BackgroundScheduler
from pagelogic.service.notify_service import notify_jobs


def notify_cronjob():
    print("Starting notification cron job...")
    notify_jobs()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    # 初始化扩展
    mail.init_app(app)
    oauth.init_app(app)
    # 注册 OAuth Provider
    import config
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        api_base_url='https://www.googleapis.com/oauth2/v3/',
        client_id=config.OAUTH_CREDENTIALS['google']['client_id'],
        client_secret=config.OAUTH_CREDENTIALS['google']['client_secret'],
        client_kwargs={'scope': 'openid email profile'}
    )

    #启动cronjob
    interval = 60 * 5
    scheduler = BackgroundScheduler()
    scheduler.add_job(notify_jobs,'interval', seconds=interval)
    scheduler.start()

    # 注册 Blueprints
    from pagelogic.index import index_bp
    from pagelogic.login import login_bp
    from pagelogic.logout import logout_bp
    from pagelogic.patient_home import patient_home_bp
    from pagelogic.test_bp import test_bp
    from pagelogic.bp import drug_bp, food_bp, plan_bp, test_connect, user_bp, drug_record_bp, food_record_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(patient_home_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(user_bp.user_bp)
    app.register_blueprint(test_connect.test_connect)
    app.register_blueprint(plan_bp.plan_bp)
    app.register_blueprint(food_bp.food_bp)
    app.register_blueprint(drug_bp.drug_bp)
    app.register_blueprint(doctor_page_bp.doctor_page_bp)
    app.register_blueprint(drug_record_bp.drug_record_bp)
    app.register_blueprint(food_record_bp.food_record_bp)

    drug_repo.get_drugs()#预热drug db入server
    drug_repo.drugs

    food_repo.get_foods()#预热food db入server
    food_repo.foods

    print(app.url_map)
    return app


app = create_app()