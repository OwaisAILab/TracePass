# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
