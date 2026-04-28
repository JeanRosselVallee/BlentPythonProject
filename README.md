"""
# DigiMarket E-commerce API

DigiMarket is a specialized PC hardware retailer diversifying into the online space. This project provides a robust REST API developed with **Flask**, using **SQLAlchemy** as an ORM and **SQLite** for data persistence.

---

## 🚀 Project Overview

The DigiMarket API manages a complete e-commerce workflow, from user registration and secure authentication to product catalog management and automated order processing with stock validation.

### Technical Stack
| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.x |
| **Backend Framework** | Flask (Factory Pattern with Blueprints) |
| **Database & ORM** | SQLite + SQLAlchemy |
| **Authentication** | JWT (JSON Web Tokens) + Werkzeug Hashing |
| **Testing** | Pytest + Requests |
| **Environment** | python-dotenv for Secret Management |

---

## 📂 Project Structure

```text
BlentPythonProject/
├── app/
│   ├── auth/            # Auth logic, routes, and decorators
│   ├── products/        # Product catalog routes
│   ├── orders/          # Order and line-item logic
│   ├── database/        # SQLAlchemy Models (model.py)
│   ├── static/          # CSS/JS for the frontend
│   ├── templates/       # HTML for the web interface
│   ├── __init__.py      # App Factory and DB initialization
│   ├── app_utils.py     # Shared utilities (JWT, DB helpers)
│   └── extensions.py    # Flask extension instances (db)
├── tests/
│   ├── test_app.py      # Main API test suite
│   ├── tests_utils.py   # Test helpers and seeding logic
│   └── pytest.log       # Automated test logs
├── .env                 # Environment variables (Secret keys)
├── pytest.ini           # Pytest configuration
├── requirements.txt     # Python dependencies
├── run.py               # Application entry point
└── instance/
    └── digimarket.db    # SQLite Database file
```

---

## 🛠️ Installation & Setup

1. **Clone the repository and enter the directory:**
   ```bash
   cd BlentPythonProject
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\\Scripts\\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```text
   SECRET_PHRASE=your_secure_random_string_here
   ```

5. **Run the Application:**
   ```bash
   python run.py
   ```
   The server will start at `http://127.0.0.1:5000`.

---

## 🔐 Security & Roles

The API implements **Role-Based Access Control (RBAC)** via JWT decorators:

- **Admin Role:** Full CRUD access to the product catalog, ability to delete items, and visibility of all customer orders.
- **Client Role:** Access to browse products, create their own orders, and view their personal order history.
- **Authentication:** Users must provide a `Bearer <token>` in the `Authorization` header for protected routes.

---

## 🧪 Testing Workflow

The project includes an automated testing suite using **Pytest**. 

### Running Tests
To run the full suite from the terminal (ensure the Flask server is running first):
```bash
python -m pytest -sv --tb=short tests/test_app.py
```

### Testing Logic
- **Seeding:** The suite automatically creates `admin@test.net` and `customer@test.net` for testing.
- **Lifecycle:** A `testing_wrapper` fixture handles DB setup before tests and performs a full cleanup (teardown) after tests finish.
- **Validation:** Every request is checked against expected HTTP status codes (e.g., 403 for unauthorized access).

---

## 📡 API Endpoints Summary

### Authentication & Users
- `POST /auth/register`: Register a new user (Email, Password, Role).
- `POST /auth/login`: Authenticate and receive a JWT.

### Product Catalog
- `GET /api/produits`: List all products (supports `?keywords=` query params).
- `GET /api/produits/<id>`: View product details.
- `POST /api/produits`: Add a new product (**Admin only**).
- `PUT /api/produits/<id>`: Update product info (**Admin only**).
- `DELETE /api/produits/<id>`: Remove a product (**Admin only**).

### Order Management
- `GET /api/commandes`: List orders (Admin sees all; Client sees their own).
- `GET /api/commandes/<id>`: View specific order details.
- `POST /api/commandes`: Create a new order (Includes stock validation).
- `PATCH /api/commandes/<id>`: Update order status or shipping address.
- `GET /api/commandes/<id>/lignes`: View order line items.
- `POST /api/commandes/<id>/lignes`: Add items to an existing order.
"""
```