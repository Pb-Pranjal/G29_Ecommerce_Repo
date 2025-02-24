from flask import Flask,render_template,request,redirect,url_for,session,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from functools import wraps
from flask_login import LoginManager,login_user,login_required,logout_user,current_user,UserMixin #this will provide methods like is_authenticated,is_active,get_id()
from werkzeug.security import generate_password_hash,check_password_hash

app=Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"]="welcome"
app.permanent_session_lifetime=timedelta(minutes=10)

# we are telling flask app  about location of database

db=SQLAlchemy(app)
login_manager=LoginManager()
login_manager.init_app(app)#we are connecting our app with flask-logout
login_manager.login_view="login"

@app.route("/")
def home():
  role=current_user.role if current_user.is_authenticated else None
  return render_template("index2.html",role2=role)
@app.route('/aboutus')
def aboutus():
    role=current_user.role if current_user.is_authenticated else None

    return render_template("aboutus.html",role2=role)
@app.route('/contactus')
def contactus():
    role=current_user.role if current_user.is_authenticated else None

    return render_template("contactus.html",role2=role)



class Student(db.Model, UserMixin):  # schema
    __tablename__ = "Student_Data"  # Corrected to use double underscores
    id = db.Column(db.Integer, primary_key=True)  # primary_key will generate unique ids
    name = db.Column(db.String(100))  # 100 means you are allowing 100 characters
    email = db.Column(db.String(100))
    password = db.Column(db.String(60))

    role=db.Column(db.String(60),default="buyer")

    def generate_password(self, simple_password):
        self.password = generate_password_hash(simple_password)

    def check_password(self, simple_password):
        return check_password_hash(self.password, simple_password)


# Database model for products
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)


# Cart model
class Cart(db.Model):
    __tablename__ = "cart"  # Corrected to use double underscores
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=1)
    user_id = db.Column(db.Integer, nullable=False)

    def __init__(self, product_id, stock=1, user_id=None):  # Corrected constructor
        self.product_id = product_id
        self.stock = stock
        self.user_id = user_id


# PurchaseHistory model
class PurchaseHistory(db.Model):
    __tablename__ = 'purchase_history'  # Corrected to use double underscores
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Student_Data.id'), nullable=False)  # Make sure 'Student_Data.id' is correct
    stock = db.Column(db.Integer, nullable=False)

    def __init__(self, product_id, stock, user_id):
        self.product_id = product_id
        self.stock = stock
        self.user_id = user_id



# Route to display the product submission form
@app.route('/submit-product', methods=['GET', 'POST'])
@login_required
def submit_product():
    if request.method == 'POST':
        seller_id = request.form.get('seller_id')
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        image_url = request.form.get('image_url')

        # Validation
        if not (seller_id and name and description and price and stock):
            flash('All fields except image URL are required!', 'error')
            return redirect(url_for('submit_product'))

        # Save to database
        try:
            product = Product(
                seller_id=int(seller_id),
                name=name,
                description=description,
                price=float(price),
                stock=int(stock),
                image_url=image_url
            )
            db.session.add(product)
            db.session.commit()
            flash('Product submitted successfully!', 'success')
            return redirect(url_for('list_products'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
            return redirect(url_for('submit_product'))

    return render_template('submit.html')
@app.route("/product")#add
@login_required
def product():
    role=current_user.role if current_user.is_authenticated else None
    products=Product.query.all()
    return render_template("product.html",products=products,role2=role)
@app.route('/products')
def list_products():
    role=current_user.role if current_user.is_authenticated else None
    products = Product.query.all()
    return render_template('productlist.html', products=products,role2=role)

# added now
@app.route("/buy_now/<int:product_id>",methods=["GET","POST"])
# @login_required
def buy_now(product_id):
    product = Product.query.get(product_id)
    
    if not product:
        return redirect(url_for('products'))
    return render_template("buynow.html",product=product)

@app.route('/update-product/<int:id>', methods=['GET', 'POST'])
def update_product(id):
    product = Product.query.get_or_404(id)  # Fetch product by ID
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.image_url = request.form.get('image_url')

        try:
            db.session.commit()  # Save the updated product
            flash('Product updated successfully!', 'success')
            return redirect(url_for('list_products'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
            return redirect(url_for('update_product', id=id))

    return render_template('updateproduct.html', product=product)



@app.route("/signup")
def signup():
    return render_template("signup.html")
   
@app.route("/signroute", methods=["GET", "POST"])
def signFunction():
    if request.method == "POST":
        name1=request.form.get("name")
        email1=request.form.get("email")
        password1=request.form.get("password")
        role1=request.form.get("role")
        if Student.query.filter_by(email=email1).first():
            flash("User already exists with this email!")
            return redirect(url_for("home"))
        user_object=Student(name=name1,email=email1,role=role1)
        user_object.generate_password(password1)
        db.session.add(user_object)
        db.session.commit()
        flash("user registered successfully")
        return redirect(url_for("login"))
    else:
        return "invalid user"

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/loginroute", methods=["GET", "POST"])
def loginFunction():
    if request.method == "POST":
        email1= request.form.get("email")
        password1= request.form.get("password")
        user_object = Student.query.filter_by(email=email1).first()
        if user_object and user_object.check_password(password1):
            login_user(user_object)
            flash("User logged in successfully")
            return redirect(url_for("home"))
        else:
            flash("Login failed. Please check your credentials.")
    return render_template("login.html")
@login_manager.user_loader
def load_user(user_id):
  return db.session.get(Student,int(user_id))

# Route for checkout
@app.route("/checkout", methods=["POST", "GET"])
@login_required
def checkout():
    user_id = current_user.id  # Get the logged-in user's ID
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    if not cart_items:
        flash("Your cart is empty. Add items before checking out!", "error")
        return redirect(url_for("view_cart"))

    # Calculate total amount
    total_amount = 0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            total_amount += item.stock * product.price

    try:
        # Save cart items to purchase history (user's profile)
        for item in cart_items:
            purchase_history = PurchaseHistory(
                product_id=item.product_id,
                stock=item.stock,
                user_id=user_id
            )
            db.session.add(purchase_history)

        # Commit the changes to save purchase history
        db.session.commit()

        # Clear the cart after successful checkout
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()

        flash(f"Checkout successful! Total amount: ₹{total_amount:.2f}. Your cart is now empty.", "success")
        return redirect(url_for("thanks"))

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred during checkout: {e}", "error")
        return redirect(url_for("view_cart"))

@app.route("/profile")
@login_required
def profile():
    user_id = current_user.id  # Get the logged-in user's ID
    purchase_history = PurchaseHistory.query.filter_by(user_id=user_id).all()
    
    purchase_details = []
    for item in purchase_history:
        product = Product.query.get(item.product_id)
        if product:
            purchase_details.append({
                'name': product.name,
                'price': product.price,
                'quantity': item.stock,
                'total': item.stock * product.price
            })

    total_spent = sum(item['total'] for item in purchase_details)
    
    return render_template("profile.html", purchase_details=purchase_details, total_spent=total_spent)

@app.route("/thankyou")
def thanks():
    return render_template("thankyou.html")  # Ensure you have a thank-you page template


@app.route("/add_to_cart/<int:product_id>", methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get(product_id)  # Retrieve the product
    if product:
        user_id = current_user.id  # Get the logged-in user's ID using Flask-Login

        # Check if the product is already in the user's cart
        existing_cart_item = Cart.query.filter_by(product_id=product.id, user_id=user_id).first()
        
        if existing_cart_item:
            existing_cart_item.stock += 1  # Increase stock if it's already in the cart
        else:
            # Add new item to the cart
            cart_item = Cart(product_id=product.id, stock=1, user_id=user_id)
            db.session.add(cart_item)
        
        db.session.commit()
        flash(f"Added {product.name} to your cart!")

        return redirect(url_for('view_cart'))
    
    flash("Product not found!")
    return redirect(url_for('product'))




@app.route("/view_cart")
@login_required
def view_cart():
    user_id = current_user.id  # Get the logged-in user's ID
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    cart_details = []

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            cart_details.append({
                'id': item.id,
                'name': product.name,
                'price': product.price,
                'quantity': item.stock,
                'total': item.stock * product.price
            })

    total_amount = sum(item['total'] for item in cart_details)

    return render_template("viewcart.html", cart_details=cart_details, total_amount=total_amount)

@app.route("/update_cart/<int:cart_id>", methods=["POST"])
# @login_required
def update_cart(cart_id):
    new_quantity = int(request.form.get("quantity"))
    cart_item = Cart.query.get(cart_id)

    if cart_item and new_quantity > 0:
        cart_item.stock = new_quantity
        db.session.commit()
        flash("Cart updated successfully!")
    else:
        flash("Invalid quantity!")

    return redirect(url_for("view_cart"))


@app.route("/remove_from_cart/<int:cart_id>")
# @login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get(cart_id)

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash("Item removed from cart!")
    else:
        flash("Item not found!")

    return redirect(url_for("view_cart"))

@app.route('/delete-product/<int:id>', methods=['POST','GET'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)  # Find the product by ID or return 404
    try:
        db.session.delete(product)  # Delete the product
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {e}', 'error')
    return redirect(url_for('list_products'))



@app.route("/logout")
def logout():
     logout_user()
     return redirect(url_for("login"))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)