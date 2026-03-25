# BlentPythonProject
DigiMarket sells PC hardware &amp; wants to diversify its activity with an online e-shop (E-commerce) via an API REST developped with Flask, SQLALchemy as ORM, an SQLite database.

# Project Overview: DigiMarket E-commerce API

DigiMarket is diversifying into e-commerce by developing a REST API to manage products, categories, orders, and users.

---

### Technical Constraints

| Category | Technology |
| :--- | :--- |
| **Language** | Python |
| **Backend Framework** | Flask (with Blueprints) |
| **Database & ORM** | SQLite with SQLAlchemy |
| **Authentication** | JWT (JSON Web Tokens) with password hashing |
| **Architecture** | Modular (Models, Controllers, Views/JSON) |

---

### API Endpoints Summary

#### 1. Authentication & Users
* **POST** `/api/auth/register`: Register a new user (Email, Password, Role).
* **POST** `/api/auth/login`: Authenticate and receive a JWT.

#### 2. Product Catalog
* **GET** `/api/produits`: List all products (Public/Client).
* **GET** `/api/produits/{id}`: View product details (Public/Client).
* **POST** `/api/produits`: Add a new product (**Admin only**).
* **PUT** `/api/produits/{id}`: Update product info (**Admin only**).
* **DELETE** `/api/produits/{id}`: Remove a product (**Admin only**).

#### 3. Order Management
* **GET** `/api/commandes`: List orders (Admin sees all; Client sees their own).
* **GET** `/api/commandes/{id}`: View specific order details.
* **POST** `/api/commandes`: Create a new order (Includes stock validation).
* **PATCH** `/api/commandes/{id}`: Update order status (**Admin only**).
* **GET** `/api/commandes/{id}/lignes`: View order line items.

---

### Key Functional Requirements

* **Roles:** * **Clients:** Browse, search, order, and track history.
    * **Admins:** Manage catalog, stock, and all customer orders.
* **Stock Logic:** System must verify availability and auto-update quantities upon order validation.
* **Security:** Role-based access control (RBAC) and protection against common vulnerabilities (SQL injection).

---

### Expected Deliverables

1. **Source Code:** Organized structure with `requirements.txt`.
2. **Documentation:** `README.md` with installation, usage, and API specs.
3. **Database:** Initialized SQLite file with test data.
4. **Testing:** Unit and functional tests for core features.
