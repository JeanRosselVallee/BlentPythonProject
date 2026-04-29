# Application Entry Point
# This script initializes and starts the Flask development server.
# It imports the 'app' instance created in the package's __init__.py file.

from app import app

if __name__ == "__main__":
    # Start the Flask development server
    # 'debug=True' enables automatic reloading & provides debugger to browser
    app.run(debug=True)
