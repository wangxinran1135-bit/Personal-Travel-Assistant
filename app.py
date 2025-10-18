from flask import Flask, request, jsonify
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Database configuration - modify parameters based on actual settings
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "PTA"
DB_USER = "postgres"
DB_PASSWORD = "2001830"

# Connect to the database
conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
conn.autocommit = True  # Enable autocommit for easier transaction handling

app = Flask(__name__)

# User registration endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body cannot be empty"}), 400
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    phone = data.get('phone')
    provider_name = data.get('provider_name')
    category = data.get('category')
    if not name or not email or not password or not role:
        return jsonify({"success": False, "message": "Missing required parameters"}), 400

    cur = conn.cursor()
    # Check if email already exists
    cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        return jsonify({"success": False, "message": "Email already registered"}), 400

    # Hash the password and store it
    pw_hash = generate_password_hash(password)
    # Insert user record
    cur.execute(
        "INSERT INTO users (name, email, password_hash, user_role, phone) VALUES (%s, %s, %s, %s, %s) RETURNING user_id",
        (name, email, pw_hash, role, phone))
    user_id = cur.fetchone()[0]

    provider_id = None
    if role == 'ServiceProvider':
        # If registering as a service provider, insert into service_providers table
        # Use provider_name or user's name as the provider name
        cur.execute(
            "INSERT INTO service_providers (user_id, name, category) VALUES (%s, %s, %s) RETURNING provider_id",
            (user_id, provider_name or name, category or None))
        provider_id = cur.fetchone()[0]

    # Construct and return user info
    user_info = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role
    }
    if provider_id:
        user_info["provider_id"] = provider_id
    return jsonify({"success": True, "user": user_info})

# User login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body cannot be empty"}), 400
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, password_hash, user_role FROM users WHERE email = %s", (email,))
    result = cur.fetchone()
    if not result:
        return jsonify({"success": False, "message": "User does not exist"}), 401
    user_id, name, email, password_hash, user_role = result
    # Verify password hash
    if not check_password_hash(password_hash, password):
        return jsonify({"success": False, "message": "Incorrect password"}), 401

    # If user is a service provider, retrieve provider_id and name
    provider_id = None
    provider_name = None
    if user_role == 'ServiceProvider':
        cur.execute("SELECT provider_id, name FROM service_providers WHERE user_id = %s", (user_id,))
        res = cur.fetchone()
        if res:
            provider_id, provider_name = res

    # Return user info
    user_info = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": user_role
    }
    if provider_id:
        user_info["provider_id"] = provider_id
        user_info["provider_name"] = provider_name
    return jsonify({"success": True, "user": user_info})

# Get service offerings endpoint
@app.route('/api/service_offerings', methods=['GET'])
def get_offerings():
    # Optional query parameter: user_id or provider_id
    provider_id = request.args.get('provider_id')
    user_id = request.args.get('user_id')
    cur = conn.cursor()
    if user_id:
        # If user_id is provided, find corresponding provider_id
        cur.execute("SELECT provider_id FROM service_providers WHERE user_id = %s", (user_id,))
        res = cur.fetchone()
        if not res:
            return jsonify({"success": False, "message": "User is not a service provider"}), 400
        provider_id = res[0]
    if provider_id:
        # Return all service offerings for this provider
        cur.execute("SELECT offering_id, title, description, category, status, created_at, updated_at "
                    "FROM service_offerings WHERE provider_id = %s", (provider_id,))
        rows = cur.fetchall()
        offerings = []
        for r in rows:
            offerings.append({
                "offering_id": r[0],
                "title": r[1],
                "description": r[2],
                "category": r[3],
                "status": r[4],
                "created_at": r[5].strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": r[6].strftime("%Y-%m-%d %H:%M:%S")
            })
        return jsonify({"success": True, "offerings": offerings})
    else:
        # If no provider specified, return all Active offerings (with provider name)
        cur.execute("SELECT o.offering_id, o.title, o.description, o.category, p.name "
                    "FROM service_offerings o JOIN service_providers p ON o.provider_id = p.provider_id "
                    "WHERE o.status = 'Active'")
        rows = cur.fetchall()
        offerings = []
        for r in rows:
            offerings.append({
                "offering_id": r[0],
                "title": r[1],
                "description": r[2],
                "category": r[3],
                "provider_name": r[4]
            })
        return jsonify({"success": True, "offerings": offerings})

# Add new service offering endpoint (ServiceProvider)
@app.route('/api/add_offering', methods=['POST'])
def add_offering():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body cannot be empty"}), 400
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description')
    category = data.get('category')
    status = data.get('status') or 'Active'
    if not user_id or not title or not description:
        return jsonify({"success": False, "message": "Missing required parameters"}), 400

    cur = conn.cursor()
    # Get provider_id for this user
    cur.execute("SELECT provider_id FROM service_providers WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    if not res:
        return jsonify({"success": False, "message": "Invalid service provider user"}), 400
    provider_id = res[0]
    # Insert new service offering
    cur.execute("INSERT INTO service_offerings (provider_id, title, description, category, status) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING offering_id",
                (provider_id, title, description, category, status))
    offering_id = cur.fetchone()[0]
    return jsonify({"success": True, "offering_id": offering_id})

# Delete service offering endpoint (ServiceProvider)
@app.route('/api/delete_offering', methods=['POST'])
def delete_offering():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body cannot be empty"}), 400
    user_id = data.get('user_id')
    offering_id = data.get('offering_id')
    if not user_id or not offering_id:
        return jsonify({"success": False, "message": "Missing required parameters"}), 400

    cur = conn.cursor()
    # Validate this offering belongs to this user's provider
    cur.execute("SELECT o.offering_id FROM service_offerings o JOIN service_providers p "
                "ON o.provider_id = p.provider_id WHERE o.offering_id = %s AND p.user_id = %s",
                (offering_id, user_id))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Not authorized to delete this offering"}), 403

    cur.execute("DELETE FROM service_offerings WHERE offering_id = %s", (offering_id,))
    return jsonify({"success": True})

# Get inventory list endpoint (ServiceProvider)
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    offering_id = request.args.get('offering_id')
    if not offering_id:
        return jsonify({"success": False, "message": "Missing offering_id parameter"}), 400
    cur = conn.cursor()
    cur.execute("SELECT inventory_id, date, capacity, available, status "
                "FROM inventories WHERE offering_id = %s ORDER BY date", (offering_id,))
    rows = cur.fetchall()
    inventory_list = []
    for r in rows:
        inventory_list.append({
            "inventory_id": r[0],
            "date": r[1].strftime("%Y-%m-%d"),
            "capacity": r[2],
            "available": r[3],
            "status": r[4]
        })
    return jsonify({"success": True, "inventory": inventory_list})

# Add or update inventory endpoint (ServiceProvider)
@app.route('/api/inventory', methods=['POST'])
def add_or_update_inventory():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body cannot be empty"}), 400
    user_id = data.get('user_id')
    offering_id = data.get('offering_id')
    date_str = data.get('date')
    capacity = data.get('capacity')
    available = data.get('available')
    if not user_id or not offering_id or not date_str or capacity is None or available is None:
        return jsonify({"success": False, "message": "Missing required parameters"}), 400

    # Verify user is provider of the offering
    cur = conn.cursor()
    cur.execute("SELECT p.provider_id FROM service_offerings o JOIN service_providers p "
                "ON o.provider_id = p.provider_id WHERE o.offering_id = %s AND p.user_id = %s",
                (offering_id, user_id))
    if not cur.fetchone():
        return jsonify({"success": False, "message": "Not authorized to manage this inventory"}), 403

    # Convert and validate date format
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"success": False, "message": "Invalid date format, should be YYYY-MM-DD"}), 400

    # Check if inventory for given date exists
    cur.execute("SELECT inventory_id FROM inventories WHERE offering_id = %s AND date = %s",
                (offering_id, date_obj))
    result = cur.fetchone()
    if result:
        # Update existing inventory record
        inventory_id = result[0]
        status = 'Open' if available > 0 else 'SoldOut'
        cur.execute("UPDATE inventories SET capacity = %s, available = %s, status = %s, last_updated = NOW() "
                    "WHERE inventory_id = %s",
                    (capacity, available, status, inventory_id))
        return jsonify({"success": True, "action": "updated"})
    else:
        # Insert new inventory record
        status = 'Open' if available > 0 else 'SoldOut'
        cur.execute("INSERT INTO inventories (offering_id, date, capacity, available, status) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (offering_id, date_obj, capacity, available, status))
        return jsonify({"success": True, "action": "inserted"})

# Start development server only when running script directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)