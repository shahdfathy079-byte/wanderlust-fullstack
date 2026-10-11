from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import os
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "http://127.0.0.1:5001",
    "http://localhost:5001",
    "http://localhost:8080",
    "http://127.0.0.1:8080"
])
app.secret_key = 'super_secret_key_here'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True

# ==================== Task 10: File Upload Config ====================

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'txt'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== Task 9: RBAC Decorators ====================

def login_required(f):
    """يتأكد إن المستخدم مسجل دخول"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required!'}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """يتأكد إن المستخدم عنده role من الأدوار المسموحة"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required!'}), 401

            user_role = session.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Forbidden: insufficient permissions',
                    'your_role': user_role,
                    'required_roles': list(allowed_roles)
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator


# ==================== Database Init ====================

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')

    # (Task 3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT DEFAULT 'fas fa-cogs'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_type TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

        # ==================== Task 11: Projects ====================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'not_started',
            client_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (project_id, user_id)
        )
    ''')

    # Seed services
    cursor.execute('SELECT COUNT(*) FROM services')
    if cursor.fetchone()[0] == 0:
        initial_services = [
            ('Flight Booking', 'Easy and fast domestic and international flight reservations.', 'fas fa-plane'),
            ('Hotel Accommodation', 'Best price guarantees for luxury and budget hotels worldwide.', 'fas fa-hotel'),
            ('Guided Tours', 'Professional tour guides and curated packages for memorable adventures.', 'fas fa-map-marked-alt')
        ]
        cursor.executemany('INSERT INTO services (title, description, icon) VALUES (?, ?, ?)', initial_services)

    # Seed destinations
    cursor.execute('SELECT COUNT(*) FROM destinations')
    if cursor.fetchone()[0] == 0:
        initial_destinations = [
            ('Paris, France', 'Experience the city of lights, culture, and exquisite cuisine.', 'images/paris.jpg'),
            ('Dubai, UAE', 'A blend of futuristic architecture, luxury shopping, and desert safaris.', 'images/dubai.jpg'),
            ('Cairo, Egypt', 'Discover the ancient pyramids and vibrant culture.', 'images/cairo.jpg')
        ]
        cursor.executemany('INSERT INTO destinations (title, description, image_url) VALUES (?, ?, ?)', initial_destinations)

    # Seed Admin & Employee (Task 9)
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash('admin123')
        emp_pass = generate_password_hash('employee123')
        cursor.execute(
            'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
            ('Admin', 'admin@wanderlust.com', admin_pass, 'admin')
        )
        cursor.execute(
            'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
            ('Employee', 'employee@wanderlust.com', emp_pass, 'employee')
        )

            # Seed clients
    cursor.execute('SELECT COUNT(*) FROM clients')
    if cursor.fetchone()[0] == 0:
        initial_clients = [
            ('Acme Corporation', 'contact@acme.com', '+1-555-0100', 'Acme Corp'),
            ('Globex Industries', 'info@globex.com', '+1-555-0200', 'Globex Inc'),
            ('Initech Solutions', 'hello@initech.com', '+1-555-0300', 'Initech')
        ]
        cursor.executemany(
            'INSERT INTO clients (name, email, phone, company) VALUES (?, ?, ?, ?)',
            initial_clients
        )

    conn.commit()
    conn.close()


# ==================== Contact ====================

@app.route('/api/contact', methods=['POST'])
def receive_contact():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    if not name or not email or not subject or not message:
        return jsonify({'error': 'All fields are required!'}), 400

    if '@' not in email:
        return jsonify({'error': 'Invalid email format!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO inquiries (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, subject, message))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Inquiry submitted and stored successfully!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Destinations CRUD ====================

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, image_url FROM destinations')
    rows = cursor.fetchall()
    conn.close()
    destinations = [{'id': r[0], 'title': r[1], 'description': r[2], 'image_url': r[3]} for r in rows]
    return jsonify(destinations), 200


@app.route('/api/destinations', methods=['POST'])
@role_required('admin')
def add_destination():
    data = request.get_json()
    title, description, image_url = data.get('title'), data.get('description'), data.get('image_url')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO destinations (title, description, image_url) VALUES (?, ?, ?)', (title, description, image_url))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Destination added successfully!'}), 201


@app.route('/api/destinations/<int:id>', methods=['PUT'])
@role_required('admin')
def update_destination(id):
    data = request.get_json()
    title, description, image_url = data.get('title'), data.get('description'), data.get('image_url')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE destinations SET title = ?, description = ?, image_url = ? WHERE id = ?', (title, description, image_url, id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Destination updated successfully!'}), 200


@app.route('/api/destinations/<int:id>', methods=['DELETE'])
@role_required('admin')
def delete_destination(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM destinations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Destination deleted successfully!'}), 200


# ==================== Auth ====================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required!'}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                       (username, email, hashed_password, 'customer'))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully!'}), 201
    except sqlite3.IntegrityError:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': 'Email already exists!'}), 400
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required!'}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password, role FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['role'] = user[3]
        return jsonify({
            'message': 'Logged in successfully!',
            'role': user[3],
            'username': user[1]
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password!'}), 401


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'username': session.get('username'),
            'role': session.get('role')
        }), 200
    return jsonify({'authenticated': False}), 401


@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, email, role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({'username': user[0], 'email': user[1], 'role': user[2]}), 200
    return jsonify({'error': 'User not found'}), 404


@app.route('/api/user/update', methods=['PUT'])
@login_required
def update_user_profile():
    data = request.get_json()
    new_username = data.get('username')

    if not new_username:
        return jsonify({'error': 'Username is required'}), 400

    user_id = session['user_id']
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
        conn.commit()
        conn.close()

        session['username'] = new_username
        return jsonify({'message': 'Profile updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully!'}), 200


# ==================== Task 6: Services CRUD ====================

@app.route('/api/services', methods=['GET'])
def get_services():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, icon FROM services')
    rows = cursor.fetchall()
    conn.close()
    services = [{'id': r[0], 'title': r[1], 'description': r[2], 'icon': r[3]} for r in rows]
    return jsonify(services), 200


@app.route('/api/services', methods=['POST'])
@role_required('admin')
def add_service():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-cogs')

    if not title or not description:
        return jsonify({'error': 'Title and description are required!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO services (title, description, icon) VALUES (?, ?, ?)', (title, description, icon))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Service added successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/services/<int:id>', methods=['PUT'])
@role_required('admin')
def update_service(id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    icon = data.get('icon', 'fas fa-cogs')

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE services SET title = ?, description = ?, icon = ? WHERE id = ?', (title, description, icon, id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Service updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/services/<int:id>', methods=['DELETE'])
@role_required('admin')
def delete_service(id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM services WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Service deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Task 7: Service Requests ====================

@app.route('/api/requests', methods=['POST'])
@login_required
def create_request():
    data = request.get_json()
    service_type = data.get('service_type')
    details = data.get('details')

    if not service_type or not details:
        return jsonify({'error': 'Service type and details are required!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO service_requests (user_id, service_type, details, status)
            VALUES (?, ?, ?, 'pending')
        ''', (session['user_id'], service_type, details))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Request submitted successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/requests/my', methods=['GET'])
@login_required
def get_my_requests():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, service_type, details, status, created_at, updated_at
        FROM service_requests
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    requests_list = [{
        'id': r[0], 'service_type': r[1], 'details': r[2],
        'status': r[3], 'created_at': r[4], 'updated_at': r[5]
    } for r in rows]
    return jsonify(requests_list), 200


@app.route('/api/admin/requests', methods=['GET'])
@role_required('admin', 'employee')
def get_all_requests():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sr.id, sr.service_type, sr.details, sr.status,
               sr.created_at, sr.updated_at,
               u.username, u.email
        FROM service_requests sr
        JOIN users u ON sr.user_id = u.id
        ORDER BY sr.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    requests_list = [{
        'id': r[0], 'service_type': r[1], 'details': r[2],
        'status': r[3], 'created_at': r[4], 'updated_at': r[5],
        'customer_name': r[6], 'customer_email': r[7]
    } for r in rows]
    return jsonify(requests_list), 200


@app.route('/api/admin/requests/<int:id>', methods=['PUT'])
@role_required('admin', 'employee')
def update_request_status(id):
    data = request.get_json()
    new_status = data.get('status')
    allowed = ['pending', 'in_progress', 'completed', 'rejected']

    if new_status not in allowed:
        return jsonify({'error': 'Invalid status!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE service_requests
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Status updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Task 9: Admin Users Management ====================

@app.route('/api/admin/users', methods=['GET'])
@role_required('admin')
def get_all_users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role FROM users ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    users = [{'id': r[0], 'username': r[1], 'email': r[2], 'role': r[3]} for r in rows]
    return jsonify(users), 200


@app.route('/api/admin/users/<int:id>/role', methods=['PUT'])
@role_required('admin')
def update_user_role(id):
    data = request.get_json()
    new_role = data.get('role')
    allowed = ['admin', 'employee', 'customer']

    if new_role not in allowed:
        return jsonify({'error': 'Invalid role!'}), 400

    if id == session.get('user_id'):
        return jsonify({'error': 'You cannot change your own role!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Role updated!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Static Files Serving ====================

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


# ==================== Task 8: Search & Filtering ====================

@app.route('/api/destinations/search', methods=['GET'])
def search_destinations():
    keyword = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    sort_by = request.args.get('sort', 'newest')

    query = "SELECT id, title, description, image_url FROM destinations WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{keyword}%"
        params.extend([like, like])

    if location:
        query += " AND (title LIKE ? OR image_url LIKE ?)"
        like_loc = f"%{location}%"
        params.extend([like_loc, like_loc])

    if sort_by == 'title_asc':
        query += " ORDER BY title ASC"
    elif sort_by == 'title_desc':
        query += " ORDER BY title DESC"
    else:
        query += " ORDER BY id DESC"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = [{
        'id': r[0], 'title': r[1], 'description': r[2], 'image_url': r[3]
    } for r in rows]

    return jsonify({
        'count': len(results),
        'filters': {
            'keyword': keyword,
            'location': location,
            'sort': sort_by
        },
        'results': results
    }), 200

# ==================== Task 10: File Management ====================

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file():
    # 1. هل فيه ملف في الـ request؟
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    # 2. هل المستخدم اختار ملف فعلاً؟
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # 3. هل الامتداد مسموح؟
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        original_name = file.filename
        ext = original_name.rsplit('.', 1)[1].lower()
        # اسم فريد عشان مفيش تعارض
        stored_name = f"{uuid.uuid4().hex}.{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_name)
        file.save(filepath)

        file_size = os.path.getsize(filepath)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_files (user_id, original_name, stored_name, file_size, file_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], original_name, stored_name, file_size, ext))
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'File uploaded successfully!',
            'file': {
                'original_name': original_name,
                'stored_name': stored_name,
                'size': file_size,
                'type': ext
            }
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/my', methods=['GET'])
@login_required
def get_my_files():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, original_name, stored_name, file_size, file_type, uploaded_at
        FROM user_files
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
    ''', (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    files = [{
        'id': r[0],
        'original_name': r[1],
        'stored_name': r[2],
        'size': r[3],
        'type': r[4],
        'uploaded_at': r[5],
        'url': f'/uploads/{r[2]}'
    } for r in rows]
    return jsonify(files), 200


@app.route('/api/files/<int:id>', methods=['DELETE'])
@login_required
def delete_file(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT stored_name FROM user_files WHERE id = ? AND user_id = ?',
                   (id, session['user_id']))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({'error': 'File not found or unauthorized'}), 404

    stored_name = row[0]
    cursor.execute('DELETE FROM user_files WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_name)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Warning: could not delete physical file: {e}")

    return jsonify({'message': 'File deleted successfully!'}), 200


# Route لخدمة الملفات المرفوعة
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== Task 11: Clients APIs ====================

@app.route('/api/clients', methods=['GET'])
@role_required('admin', 'employee')
def get_clients():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, phone, company, created_at FROM clients ORDER BY name')
    rows = cursor.fetchall()
    conn.close()

    clients = [{
        'id': r[0], 'name': r[1], 'email': r[2],
        'phone': r[3], 'company': r[4], 'created_at': r[5]
    } for r in rows]
    return jsonify(clients), 200


@app.route('/api/clients', methods=['POST'])
@role_required('admin')
def create_client():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email', '')
    phone = data.get('phone', '')
    company = data.get('company', '')

    if not name:
        return jsonify({'error': 'Client name is required!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO clients (name, email, phone, company) VALUES (?, ?, ?, ?)',
            (name, email, phone, company)
        )
        conn.commit()
        client_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Client created!', 'id': client_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:id>', methods=['PUT'])
@role_required('admin')
def update_client(id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email', '')
    phone = data.get('phone', '')
    company = data.get('company', '')

    if not name:
        return jsonify({'error': 'Client name is required!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE clients SET name = ?, email = ?, phone = ?, company = ? WHERE id = ?',
            (name, email, phone, company, id)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Client updated!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:id>', methods=['DELETE'])
@role_required('admin')
def delete_client(id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Client deleted!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Task 11: Projects APIs ====================

@app.route('/api/projects', methods=['GET'])
@role_required('admin', 'employee')
def get_projects():
    # Admin يشوف كل المشاريع، Employee يشوف اللي هو متعيّن فيها بس
    user_role = session.get('role')
    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    base_query = '''
        SELECT p.id, p.title, p.description, p.status,
               p.client_id, c.name AS client_name,
               p.created_at, p.updated_at
        FROM projects p
        LEFT JOIN clients c ON p.client_id = c.id
    '''

    if user_role == 'admin':
        cursor.execute(base_query + ' ORDER BY p.created_at DESC')
    else:
        cursor.execute(base_query + '''
            JOIN project_members pm ON pm.project_id = p.id
            WHERE pm.user_id = ?
            ORDER BY p.created_at DESC
        ''', (user_id,))

    rows = cursor.fetchall()

    # نجيب الأعضاء لكل مشروع
    projects = []
    for r in rows:
        cursor.execute('''
            SELECT u.id, u.username, u.role
            FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = ?
        ''', (r[0],))
        members = [{'id': m[0], 'username': m[1], 'role': m[2]} for m in cursor.fetchall()]

        projects.append({
            'id': r[0], 'title': r[1], 'description': r[2], 'status': r[3],
            'client_id': r[4], 'client_name': r[5],
            'created_at': r[6], 'updated_at': r[7],
            'members': members,
            'members_count': len(members)
        })

    conn.close()
    return jsonify(projects), 200


@app.route('/api/projects/<int:id>', methods=['GET'])
@role_required('admin', 'employee')
def get_project(id):
    user_role = session.get('role')
    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.id, p.title, p.description, p.status,
               p.client_id, c.name AS client_name,
               p.created_at, p.updated_at
        FROM projects p
        LEFT JOIN clients c ON p.client_id = c.id
        WHERE p.id = ?
    ''', (id,))
    r = cursor.fetchone()

    if not r:
        conn.close()
        return jsonify({'error': 'Project not found'}), 404

    # لو employee، لازم يكون متعيّن في المشروع
    if user_role == 'employee':
        cursor.execute('SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ?', (id, user_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'You are not assigned to this project'}), 403

    # نجيب الأعضاء
    cursor.execute('''
        SELECT u.id, u.username, u.role
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id = ?
    ''', (id,))
    members = [{'id': m[0], 'username': m[1], 'role': m[2]} for m in cursor.fetchall()]
    conn.close()

    project = {
        'id': r[0], 'title': r[1], 'description': r[2], 'status': r[3],
        'client_id': r[4], 'client_name': r[5],
        'created_at': r[6], 'updated_at': r[7],
        'members': members
    }
    return jsonify(project), 200


@app.route('/api/projects', methods=['POST'])
@role_required('admin')
def create_project():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    status = data.get('status', 'not_started')
    client_id = data.get('client_id')

    allowed_statuses = ['not_started', 'in_progress', 'completed', 'on_hold']

    if not title:
        return jsonify({'error': 'Title is required!'}), 400
    if status not in allowed_statuses:
        return jsonify({'error': 'Invalid status!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (title, description, status, client_id, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, status, client_id, session['user_id']))
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Project created!', 'id': project_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:id>', methods=['PUT'])
@role_required('admin', 'employee')
def update_project(id):
    user_role = session.get('role')
    user_id = session.get('user_id')

    # Employee لازم يكون متعيّن
    if user_role == 'employee':
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ?', (id, user_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'You are not assigned to this project'}), 403
        conn.close()

    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    status = data.get('status', 'not_started')
    client_id = data.get('client_id')

    allowed_statuses = ['not_started', 'in_progress', 'completed', 'on_hold']

    if not title:
        return jsonify({'error': 'Title is required!'}), 400
    if status not in allowed_statuses:
        return jsonify({'error': 'Invalid status!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE projects
            SET title = ?, description = ?, status = ?, client_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, description, status, client_id, id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Project updated!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:id>', methods=['DELETE'])
@role_required('admin')
def delete_project(id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM project_members WHERE project_id = ?', (id,))
        cursor.execute('DELETE FROM projects WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Project deleted!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Task 11: Project Members ====================

@app.route('/api/projects/<int:id>/members', methods=['POST'])
@role_required('admin')
def add_project_member(id):
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required!'}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO project_members (project_id, user_id) VALUES (?, ?)',
            (id, user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Member added!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Member already in project!'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:id>/members/<int:user_id>', methods=['DELETE'])
@role_required('admin')
def remove_project_member(id, user_id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM project_members WHERE project_id = ? AND user_id = ?',
            (id, user_id)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Member removed!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Task 11: Dashboard Stats ====================

@app.route('/api/projects/stats', methods=['GET'])
@role_required('admin', 'employee')
def project_stats():
    user_role = session.get('role')
    user_id = session.get('user_id')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if user_role == 'admin':
        cursor.execute('SELECT COUNT(*) FROM projects')
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'in_progress'")
        in_progress = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'completed'")
        completed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'not_started'")
        not_started = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'on_hold'")
        on_hold = cursor.fetchone()[0]
    else:
        cursor.execute('SELECT COUNT(*) FROM project_members WHERE user_id = ?', (user_id,))
        total = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM projects p
            JOIN project_members pm ON pm.project_id = p.id
            WHERE pm.user_id = ? AND p.status = 'in_progress'
        ''', (user_id,))
        in_progress = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM projects p
            JOIN project_members pm ON pm.project_id = p.id
            WHERE pm.user_id = ? AND p.status = 'completed'
        ''', (user_id,))
        completed = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM projects p
            JOIN project_members pm ON pm.project_id = p.id
            WHERE pm.user_id = ? AND p.status = 'not_started'
        ''', (user_id,))
        not_started = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM projects p
            JOIN project_members pm ON pm.project_id = p.id
            WHERE pm.user_id = ? AND p.status = 'on_hold'
        ''', (user_id,))
        on_hold = cursor.fetchone()[0]

    conn.close()
    return jsonify({
        'total': total,
        'in_progress': in_progress,
        'completed': completed,
        'not_started': not_started,
        'on_hold': on_hold
    }), 200


# ==================== Task 11: Users list (للإسناد) ====================

@app.route('/api/users/list', methods=['GET'])
@role_required('admin', 'employee')
def users_list():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users WHERE role IN ('admin', 'employee') ORDER BY username")
    rows = cursor.fetchall()
    conn.close()
    users = [{'id': r[0], 'username': r[1], 'email': r[2], 'role': r[3]} for r in rows]
    return jsonify(users), 200

# ==================== Run ====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)