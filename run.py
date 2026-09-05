
from app import create_app

# Creates the Flask application instance using the project application factory.
app = create_app()

# Starts the local development server without exposing Flask's interactive debugger by default.

if __name__ == "__main__":
    app.run(debug=False)
