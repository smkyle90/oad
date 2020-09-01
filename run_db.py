from project import create_app, db

db.create_all(
    app=create_app()
)  # pass the create_app result so Flask-SQLAlchemy gets the configuration.
