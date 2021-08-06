from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message
import hmac
import sqlite3


class Users(object):
    def __init__(self, id, email, username, password):
        self.id = id
        self.email = email
        self.username = username
        self.password = password


class Products(object):
    def __init__(self, product_id, name, price, description, product_type):
        self.id = product_id
        self.name = name
        self.price = price
        self.description = description
        self.type = product_type


def init_users_table():
    conn = sqlite3.connect('products.db')
    print("Opened database successfully")

    conn.execute('''CREATE TABLE IF NOT EXISTS Users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 surname TEXT NOT NULL,
                 address TEXT NOT NULL,
                 email TEXT NOT NULL,
                 username TEXT NOT NULL,
                 password TEXT NOT NULL);''')
    print("user table created successfully")
    conn.close()


def fetch_users():
    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM Users''')
        customers = cursor.fetchall()

        new_data = []

        for data in customers:
            print(data)
            new_data.append(Users(data[0], data[5], data[6]))
    return new_data

def init_products_table():
    with sqlite3.connect("products.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS Products(product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                     product_name TEXT NOT NULL,
                     price INTEGER NOT NULL,
                     description TEXT NOT NULL,
                     type TEXT NOT NULL,
                     quantity INTEGER NOT NULL,
                     total INTEGER NOT NULL);''')
        print("products table created successfully")


def fetch_products():
    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products")
        items = cursor.fetchall()

        new_item = []

        for data in items:
            print(data)
            new_item.append(Products(data[0], data[1], data[2], data[3], data[4]))
        return new_item


init_users_table()
init_products_table()
users = fetch_users()
products = fetch_products()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

product_table = {p.name: p for p in products}
productid_table = {p.id: p for p in products}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
mail = Mail(app)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'kamvelihle.buka2907@gmail.com'
app.config['MAIL_PASSWORD'] = 'LeeBuka2907'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

jwt = JWT(app, authenticate, identity)

@app.route('/', methods=["GET"])
def home():
    return '''<h1>A Proper List of Products</h1>
<p>A prototype API for displaying products sold at a Point of Sale system.</p>'''

@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity

@app.errorhandler(404)
def page_not_found():
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/auth', methods=["GET"])
def auth():
    return '''if you can see this, this website is indeed now working.'''

@app.route('/send-email', methods=['GET', 'POST'])
def index():
    if request.method=='POST':
        message = Message('Hello Message', sender='kamvelihle.buka2907@gmail.com', recipients=['kamvelihle.buka2907@gmail.com'])
        message.body = "Just confirming your order and notifying that it will be delivered soon."
        mail.send(message)
        return "Send email"

@app.route('/register/', methods=["POST"])
def user_registration():
    response = {}

    first_name = request.form['name']
    last_name = request.form['surname']
    address = request.form['address']
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    with sqlite3.connect('products.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Users(
                           name,
                           surname,
                           address,
                           email,
                           username,
                           password) VALUES(?, ?, ?, ?, ?, ?);''',(first_name, last_name, address, email, username, password))
        conn.commit()
        response["message"] = "success"
        response["status_code"] = 201
        return jsonify(response)


@app.route('/view-profile/<int:user_id>', methods=["GET"])
def view_profile(user_id):
    response = {}

    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE user_id=?" + int(user_id))

        response["status_code"] = 200
        response["description"] = "Profile retrieved successfully"
        response["data"] = cursor.fetchone()

    return jsonify(response)


@app.route('/create-products', methods=["POST"])
def create_products():
    response = {}

    name = request.form['product_name']
    price = request.form['price']
    desc = request.form['description']
    product_type = request.form['type']
    quantity = request.form['quantity']

    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Products(
                           product_name,
                           price,
                           description,
                           type,
                           quantity) VALUES (?, ?, ?, ?, ?)''',(name, price, desc, product_type, quantity))
        conn.commit()
        conn.close()
        response["status_code"] = 201
        response["description"] = "Items created successfully"
        return response


@app.route('/show-products')
def show_products():
    response = {}

    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products")

        response["status_code"] = 200
        response["description"] = "Displaying all items successfully"
        response["data"] = cursor.fetchall()
    return jsonify(response)


@app.route('/delete-products/<int:product_id>', methods=["DELETE"])
def delete_products(product_id):
    response = {}
    with sqlite3.connect("products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE id=?")
        conn.commit()
        response['status_code'] = 200
        response['message'] = "Items successfully deleted"

    return jsonify(response)


@app.route('/edit-products/<int:product_id>', methods=["POST"])
def edit_products(product_id):
    response = {}
    incoming_data = dict(request.json)
    put_data = {}
    if incoming_data.get("price") is not None:
        put_data["price"] = incoming_data.get("price")
        with sqlite3.connect("products.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Products SET price=? WHERE id=?", (put_data["price"], product_id))
            conn.commit()
            conn.close()
            response['message'] = "Update was successful"
            response['status_code'] = 200
        return response

    if incoming_data.get("quantity") is not None:
        put_data["quantity"] = incoming_data.get("quantity")
        with sqlite3.connect("products.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Products SET quantity=? WHERE id=?", (put_data["quantity"], product_id))
            conn.commit()
            response['message'] = "Update was successful"
            response['status_code'] = 200

        return jsonify(response)

    new_price = int(incoming_data.get("price"))
    new_quantity = int(incoming_data.get("quantity"))
    new_total = new_price * new_quantity
    if incoming_data.get("total") is not None:
        put_data["total"] = incoming_data.get("total")
        with sqlite3.connect("products.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Products SET total WHERE id=?", (new_total, product_id))
            response['status_code'] = 200
            response['message'] = "Update was successful"
        return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False)
