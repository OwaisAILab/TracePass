# TracePass code note: This module implements the run.py part of the application.
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
