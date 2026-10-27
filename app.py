import os
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps
from urllib.parse import quote_plus

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key-before-deployment")

# Configure MySQL in .env. Example:
# mysql+pymysql://username:password@localhost:3306/ecommerce_db
database_url = os.getenv("DATABASE_URL")
if not database_url:
    db_user = quote_plus(os.getenv("MYSQL_USER", "root"))
    db_password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    db_port = os.getenv("MYSQL_PORT", "3306")
    db_name = os.getenv("MYSQL_DATABASE", "ecommerce_db")
    database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
if database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(1000), nullable=False)
    category = db.Column(db.String(80), nullable=False, default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship("Product")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="Order placed")
    customer_phone = db.Column(db.String(30), nullable=True)
    address_line1 = db.Column(db.String(255), nullable=True)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    delivery_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")
    user = db.relationship("User")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    product_name = db.Column(db.String(140), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(1000), nullable=False)


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@app.context_processor
def inject_globals():
    user = current_user()
    cart_count = 0
    if user:
        cart_count = sum(item.quantity for item in CartItem.query.filter_by(user_id=user.id).all())
    return {"current_user": user, "cart_count": cart_count}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash("Admin access is required.", "danger")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.created_at.desc()).all()
    categories = [row[0] for row in db.session.query(Product.category).distinct().order_by(Product.category).all()]
    return render_template("index.html", products=products, categories=categories, q=q, selected_category=category)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("admin_dashboard" if current_user().is_admin else "index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            flash(f"Welcome back, {user.name}!", "success")
            destination = request.args.get("next")
            if user.is_admin:
                return redirect(url_for("admin_dashboard"))
            return redirect(destination if destination and destination.startswith("/") else url_for("index"))
        flash("Email or password is incorrect.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)
    return render_template("product.html", product=product)


@app.post("/cart/add/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = db.get_or_404(Product, product_id)
    try:
        quantity = max(1, int(request.form.get("quantity", 1)))
    except ValueError:
        quantity = 1
    if product.stock < 1:
        flash("This item is currently out of stock.", "warning")
    elif quantity > product.stock:
        flash(f"Only {product.stock} item(s) are currently available.", "warning")
    else:
        item = CartItem.query.filter_by(user_id=current_user().id, product_id=product.id).first()
        if item:
            item.quantity = min(item.quantity + quantity, product.stock)
        else:
            db.session.add(CartItem(user_id=current_user().id, product_id=product.id, quantity=quantity))
        db.session.commit()
        flash("Item added to your cart.", "success")
    return redirect(request.referrer or url_for("index"))


@app.post("/product/<int:product_id>/action")
@login_required
def product_action(product_id):
    product = db.get_or_404(Product, product_id)
    try:
        quantity = int(request.form.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    quantity = max(1, quantity)
    intent = request.form.get("intent", "cart")
    if product.stock < 1:
        flash("This item is currently out of stock.", "warning")
        return redirect(url_for("product_detail", product_id=product.id))
    if quantity > product.stock:
        flash(f"Only {product.stock} item(s) are currently available.", "warning")
        return redirect(url_for("product_detail", product_id=product.id))
    if intent == "buy":
        return redirect(url_for("checkout", product_id=product.id, quantity=quantity))
    item = CartItem.query.filter_by(user_id=current_user().id, product_id=product.id).first()
    if item:
        item.quantity = min(item.quantity + quantity, product.stock)
    else:
        db.session.add(CartItem(user_id=current_user().id, product_id=product.id, quantity=quantity))
    db.session.commit()
    flash("Item added to your cart.", "success")
    return redirect(url_for("product_detail", product_id=product.id))


@app.route("/cart")
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user().id).all()
    total = sum(float(item.product.price) * item.quantity for item in items if item.product)
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/update/<int:item_id>")
@login_required
def update_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user().id).first_or_404()
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        quantity = 1
    if quantity <= 0:
        db.session.delete(item)
    elif quantity > item.product.stock:
        flash(f"Only {item.product.stock} item(s) are available.", "warning")
    else:
        item.quantity = quantity
    db.session.commit()
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:item_id>")
@login_required
def remove_cart_item(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user().id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    direct_product = None
    direct_quantity = 1
    product_id = request.values.get("product_id", type=int)
    if product_id:
        direct_product = db.session.get(Product, product_id)
        if not direct_product:
            abort(404)
        direct_quantity = request.values.get("quantity", 1, type=int) or 1
        if direct_quantity < 1:
            direct_quantity = 1
        if direct_quantity > direct_product.stock:
            flash(f"Only {direct_product.stock} item(s) are currently available.", "warning")
            return redirect(url_for("product_detail", product_id=direct_product.id))
        checkout_items = [(direct_product, direct_quantity)]
    else:
        cart_items = CartItem.query.filter_by(user_id=current_user().id).all()
        checkout_items = [(item.product, item.quantity) for item in cart_items if item.product]
        if not checkout_items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

    if request.method == "GET":
        total = sum(float(product.price) * quantity for product, quantity in checkout_items)
        return render_template("checkout.html", checkout_items=checkout_items, total=total,
                               direct_product=direct_product, direct_quantity=direct_quantity)

    customer_phone = request.form.get("customer_phone", "").strip()
    address_line1 = request.form.get("address_line1", "").strip()
    address_line2 = request.form.get("address_line2", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    postal_code = request.form.get("postal_code", "").strip()
    delivery_instructions = request.form.get("delivery_instructions", "").strip()
    if not all([customer_phone, address_line1, city, state, postal_code]):
        flash("Please fill in your phone number and all required delivery address fields.", "danger")
        return render_template("checkout.html", checkout_items=checkout_items,
                               total=sum(float(product.price) * quantity for product, quantity in checkout_items),
                               direct_product=direct_product, direct_quantity=direct_quantity,
                               submitted=request.form)
    # Recheck stock on submission so a stale checkout cannot oversell stock.
    for product, quantity in checkout_items:
        if quantity > product.stock:
            flash(f"{product.name}: only {product.stock} item(s) remain. Please review your order.", "danger")
            return redirect(url_for("product_detail", product_id=product.id) if direct_product else url_for("cart"))

    total = sum(product.price * quantity for product, quantity in checkout_items)
    order = Order(user_id=current_user().id, total=total, status="Order placed",
                  customer_phone=customer_phone, address_line1=address_line1,
                  address_line2=address_line2, city=city, state=state, postal_code=postal_code,
                  delivery_instructions=delivery_instructions)
    db.session.add(order)
    db.session.flush()
    for product, quantity in checkout_items:
        product.stock -= quantity
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                                 price=product.price, quantity=quantity, image_url=product.image_url))
    if not direct_product:
        CartItem.query.filter_by(user_id=current_user().id).delete()
    db.session.commit()
    flash(f"Order #{order.id} placed successfully. This demo does not process real payments.", "success")
    return redirect(url_for("order_detail", order_id=order.id))


@app.route("/orders")
@login_required
def orders():
    orders_list = Order.query.filter_by(user_id=current_user().id).order_by(Order.created_at.asc()).all()
    return render_template("orders.html", orders=orders_list)


@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user().id).first_or_404()
    return render_template("order_detail.html", order=order)


@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html",
                           product_count=Product.query.count(), order_count=Order.query.count(),
                           user_count=User.query.filter_by(is_admin=False).count(),
                           recent_orders=Order.query.order_by(Order.created_at.asc()).limit(8).all(),
                           products=Product.query.order_by(Product.created_at.asc()).all())


@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("admin_order_detail.html", order=order)


@app.route("/admin/products/new", methods=["GET", "POST"])
@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_form(product_id=None):
    product = db.session.get(Product, product_id) if product_id else None
    if product_id and not product:
        abort(404)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        image_url = request.form.get("image_url", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        try:
            price = float(request.form.get("price", "0"))
            stock = int(request.form.get("stock", "0"))
        except ValueError:
            price, stock = -1, -1
        if not name or not image_url.startswith(("https://", "http://")) or price < 0 or stock < 0:
            flash("Please enter a name, valid HTTP(S) image URL, non-negative price and stock.", "danger")
        else:
            if not product:
                product = Product(name=name, description=description, price=price, stock=stock,
                                  image_url=image_url, category=category)
                db.session.add(product)
            else:
                product.name, product.description, product.price = name, description, price
                product.stock, product.image_url, product.category = stock, image_url, category
            db.session.commit()
            flash("Product saved successfully.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("admin_product_form.html", product=product)


@app.post("/admin/products/<int:product_id>/delete")
@admin_required
def admin_delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    # Existing order history remains intact because order items store a product-name snapshot.
    CartItem.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash("Product removed.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/orders/<int:order_id>/status")
@admin_required
def admin_update_order_status(order_id):
    order = db.get_or_404(Order, order_id)
    status = request.form.get("status", "")
    allowed = {"Order placed", "Processing", "Shipped", "Out for delivery", "Delivered", "Cancelled"}
    if status in allowed:
        order.status = status
        db.session.commit()
        flash(f"Order #{order.id} status updated.", "success")
    else:
        flash("Invalid order status.", "danger")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.cli.command("create-admin")
def create_admin():
    """Create or promote an administrator: flask --app app create-admin"""
    import getpass
    email = input("Admin email: ").strip().lower()
    name = input("Admin name: ").strip() or "Administrator"
    password = getpass.getpass("Admin password (8+ characters): ")
    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, password_hash=generate_password_hash(password), is_admin=True)
        db.session.add(user)
    else:
        user.name = name
        user.password_hash = generate_password_hash(password)
        user.is_admin = True
    db.session.commit()
    print("Admin account is ready. Sign in at /login.")


@app.cli.command("seed-products")
def seed_products():
    """Add a few sample products if the product table is empty."""
    if Product.query.first():
        print("Products already exist; no sample data added.")
        return
    samples = [
        ("Everyday Backpack", "A lightweight backpack for daily use.", 1299, 15, "Accessories", "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80"),
        ("Wireless Headphones", "Comfortable over-ear headphones for music and calls.", 2499, 12, "Electronics", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80"),
        ("Classic Sneakers", "Clean everyday sneakers with a versatile look.", 1899, 20, "Fashion", "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80"),
        ("Desk Lamp", "Modern lamp for your study or work desk.", 999, 8, "Home", "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80"),
    ]
    for name, description, price, stock, category, image_url in samples:
        db.session.add(Product(name=name, description=description, price=price, stock=stock,
                               category=category, image_url=image_url))
    db.session.commit()
    print("Sample products added.")


def migrate_order_delivery_columns():
    """Add delivery fields to existing databases without deleting existing orders."""
    inspector = inspect(db.engine)
    if "order" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("order")}
    additions = {
        "customer_phone": "VARCHAR(30) NULL",
        "address_line1": "VARCHAR(255) NULL",
        "address_line2": "VARCHAR(255) NULL",
        "city": "VARCHAR(100) NULL",
        "state": "VARCHAR(100) NULL",
        "postal_code": "VARCHAR(20) NULL",
        "delivery_instructions": "TEXT NULL",
    }
    quote = "`" if db.engine.dialect.name == "mysql" else '"'
    with db.engine.begin() as connection:
        for column_name, sql_type in additions.items():
            if column_name not in existing:
                connection.execute(text(f"ALTER TABLE {quote}order{quote} ADD COLUMN {quote}{column_name}{quote} {sql_type}"))


with app.app_context():
    db.create_all()
    migrate_order_delivery_columns()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
