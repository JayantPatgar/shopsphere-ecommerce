# ShopSphere — Python Full Stack E-commerce Demo

A responsive e-commerce starter project using **HTML, CSS, JavaScript, Python Flask and MySQL**.

## Features
- Customer registration and login (passwords are hashed).
- Product listing, search and category filter.
- Product details, cart quantity updates and removal.
- Buy Now direct checkout and cart checkout with a customer delivery-address form.
- Orders save phone number, delivery address, city, state, PIN code and delivery instructions in MySQL.
- Admin can view complete customer and delivery details for each order and update order status.
- Demo checkout creates an order and reduces stock.
- Customer order history and order status tracking.
- Separate admin dashboard to add, edit, and delete products.
- Admin can change a product's image by entering an online HTTP(S) image URL.
- Admin can update order statuses: Order placed, Processing, Shipped, Out for delivery, Delivered, Cancelled.
- Responsive layout for desktop, tablet and mobile.

> **Important:** This is a learning/demo project. Checkout does not charge money and is not connected to a payment gateway. This update automatically adds delivery columns to an existing order table without deleting existing orders. Before production use, add CSRF protection, rate limiting, secure production configuration, HTTPS, formal database migrations, payment integration and proper operational monitoring.

## Requirements
- Python 3.10+
- MySQL Server 8+
- VS Code (recommended)

## 1. Create the database
Open MySQL Workbench or MySQL command line and run:

```sql
CREATE DATABASE ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 2. Open the project in VS Code
Extract the ZIP, open the `python_full_stack_ecommerce` folder in VS Code, then open a PowerShell terminal in that folder.

## 3. Create and activate a virtual environment (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in the current terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Configure MySQL
Copy `.env.example` to `.env` and set your own MySQL username and password. Example for a typical local MySQL installation:

```env
SECRET_KEY=use-a-long-random-value-here
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_mysql_password
MYSQL_DATABASE=ecommerce_db
```

Do not share or commit your `.env` file. The application creates its tables when it starts.

## 5. Add sample products

```powershell
flask --app app seed-products
```

## 6. Create the admin account

```powershell
flask --app app create-admin
```

Enter the admin email, name and password when prompted. This creates/promotes an admin account. Do not use a weak password.

## 7. Start the website

```powershell
python run.py
```

Open http://127.0.0.1:5000 in your browser.

## How to use
1. Register a normal customer account from **Create account**.
2. Log in and browse/search products.
3. On a product page, choose **Buy now** to purchase that item directly, or **Add to cart** to keep shopping.
4. At checkout, enter a phone number and delivery address, then place the demo order. Cart checkout asks for the same delivery details. No real payment is processed.
5. Open **My orders** to view order status and the saved delivery address.
6. Sign in using the admin account and open **Admin**. Use **View details** beside an order to see customer contact and delivery details, ordered items and total; update its status there.
7. Use **Add product** or **Edit** to manage products. Paste a direct, publicly accessible image URL into the **Image URL** field. A direct URL should point to an image file or a website endpoint that returns an image; a webpage link to a photo is not always a direct image URL.

## Troubleshooting
- **Can't connect to MySQL:** make sure MySQL Server is running and credentials/database name in `.env` are correct.
- **Unknown database:** run the `CREATE DATABASE` SQL above.
- **Image not showing:** test the image URL in a browser; use a direct public HTTPS image URL. Some image hosts block hotlinking.
- **Admin page redirects to login:** create the admin with `flask --app app create-admin`, then sign in using that account.
- **Port 5000 busy:** change the port in `run.py` to `5001`.

## Project structure

```text
python_full_stack_ecommerce/
├── app.py
├── run.py
├── requirements.txt
├── .env.example
├── README.md
├── templates/
└── static/
    ├── css/style.css
    └── js/main.js
```
