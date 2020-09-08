"""App entry point."""
from oad import create_app

app = create_app()

if __name__ == "__main__":
    app.run()