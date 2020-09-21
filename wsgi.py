"""App entry point."""
from oad import create_app

application = create_app()

# if __name__ == "__main__":
#     app.run()

"""
Run this to intialise Db

from oad import db, create_app
db.create_all(app=create_app())

"""
