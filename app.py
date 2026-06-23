from flask import *
import pymysql
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "ecommerce"

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

connection = pymysql.connect(
    host="localhost",
    user="root",
    password="maneprachi2007",
    database="ecommerce_project"
)

# Home page

@app.route('/')
def home():

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM products"
    )

    products = cursor.fetchall()

    return render_template(
        'products.html',
        products=products
    )

# Register page

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (name,email,password,role)
            VALUES(%s,%s,%s,'user')
            """,
            (name,email,password)
        )

        connection.commit()

        return redirect('/login')

    return render_template('register.html')


# Login page

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=%s
            AND password=%s
            """,
            (email,password)
        )

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['role'] = user[4]

            return redirect('/dashboard')

    return render_template('login.html')

# Add product page

@app.route('/add_product', methods=['GET','POST'])
def add_product():

    if session['role'] != 'Administrator':
        return "Access Denied"

    if request.method == 'POST':

        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']

        image = request.files['image']

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO products
            (product_name,description,price,image)
            VALUES(%s,%s,%s,%s)
            """,
            (
                product_name,
                description,
                price,
                filename
            )
        )

        connection.commit()

        return redirect('/')

    return render_template('add_product.html')

# Add to cart page

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    user_id = session['user_id']

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO cart
        (user_id,product_id,quantity)
        VALUES(%s,%s,1)
        """,
        (user_id,id)
    )

    connection.commit()

    return redirect('/')

# View cart page

@app.route('/cart')
def cart():

    cursor = connection.cursor()

    cursor.execute("""
    SELECT *
    FROM cart
    JOIN products
    ON cart.product_id=products.product_id
    """)

    cart_items = cursor.fetchall()

    return render_template(
        'cart.html',
        cart_items=cart_items
    )

# Orders page

@app.route('/orders')
def orders():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT * FROM orders
        WHERE user_id=%s
        """,
        (user_id,)
    )

    orders = cursor.fetchall()

    return render_template(
        'orders.html',
        orders=orders
    )

# Place order page

@app.route('/place_order')
def place_order():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cursor = connection.cursor()

    # Calculate total amount from cart
    cursor.execute(
        """
        SELECT SUM(products.price * cart.quantity)
        FROM cart
        JOIN products
        ON cart.product_id = products.product_id
        WHERE cart.user_id = %s
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    total_amount = result[0]

    if total_amount is None:
        total_amount = 0

    # Insert order
    cursor.execute(
        """
        INSERT INTO orders
        (user_id, total_amount, order_date)
        VALUES(%s, %s, CURDATE())
        """,
        (user_id, total_amount)
    )

    # Clear cart after order
    cursor.execute(
        """
        DELETE FROM cart
        WHERE user_id = %s
        """,
        (user_id,)
    )

    connection.commit()

    return redirect('/orders')

# upload image

from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )

# Edit product page

@app.route('/edit_product/<int:id>', methods=['GET','POST'])
def edit_product(id):

    if session['role'] != 'Administrator':
        return "Access Denied"

    cursor = connection.cursor()

    if request.method == 'POST':

        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']

        cursor.execute(
            """
            UPDATE products
            SET product_name=%s,
                description=%s,
                price=%s
            WHERE product_id=%s
            """,
            (product_name,
             description,
             price,
             id)
        )

        connection.commit()

        return redirect('/')

    cursor.execute(
        "SELECT * FROM products WHERE product_id=%s",
        (id,)
    )

    product = cursor.fetchone()

    return render_template(
        'edit_product.html',
        product=product
    )    

# Delete product page

@app.route('/delete_product/<int:id>')
def delete_product(id):

    if session['role'] != 'Administrator':
        return "Access Denied"

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM products WHERE product_id=%s",
        (id,)
    )

    connection.commit()

    return redirect('/')

# search page

@app.route('/search')
def search():

    keyword = request.args.get('keyword')

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT * FROM products
        WHERE product_name LIKE %s
        """,
        ('%' + keyword + '%',)
    )

    products = cursor.fetchall()

    return render_template(
        'products.html',
        products=products
    )

# Dashboard page

@app.route('/dashboard')
def dashboard():

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM products"
    )

    products = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )

    orders = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        users=users,
        products=products,
        orders=orders
    )        

# Logout page

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


if __name__ == "__main__":
    app.run(debug=True)







