from flask import Flask
from extensions import mail, oauth
from pagelogic.repo import drug_repo


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

    # 注册 Blueprints
    from pagelogic.index import index_bp
    from pagelogic.login import login_bp
    from pagelogic.logout import logout_bp
    from pagelogic.doctor_home import doctor_home_bp
    from pagelogic.patient_home import patient_home_bp
    from pagelogic.test_bp import test_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(doctor_home_bp)
    app.register_blueprint(patient_home_bp)
    app.register_blueprint(test_bp)

    drug_repo.get_drugs()#预热drug db入server
    drug_repo.drugs

    food_repo.get_foods()#预热food db入server
    food_repo.foods

    return app


app = create_app()