import time
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.combining import OrTrigger
# from apscheduler.triggers.cron import CronTrigger

# from .scheduled import add_user_points, update_player_earnings, set_state
# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
# init the scheduler to run the DB updates.
# sched = BackgroundScheduler(daemon=True)


def create_app():
    # TODO: Add scheduling
    # trigger = OrTrigger([CronTrigger(day_of_week='mon', hour=10)])
    # sched.add_job(func=set_state, trigger='interval', seconds=)
    # sched.add_job(func=add_user_points,  args=[db], trigger=trigger)
    # sched.add_job(func=update_player_earnings,  args=[db], trigger='interval', seconds=10)
    # sched.start()

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "1234"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app
