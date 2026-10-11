# 🌍 Wanderlust — Full-Stack Travel Agency & Project Management Platform

A comprehensive full-stack web application that combines a travel agency platform with an internal client project management system. Built as the final project for the Full-Stack Development Track at Voltix.

---

## 📖 Project Overview

**Wanderlust** is a full-stack platform built with **Flask (Python)**, **SQLite**, and **vanilla JavaScript**. The application serves two main purposes:

1. **Customer-Facing Travel Agency** — Browse destinations, book services, submit inquiries, and upload documents.
2. **Internal Project Management** — Manage clients, projects, team assignments, and track project progress.

The platform implements **Role-Based Access Control (RBAC)** with three distinct user roles, each with its own permissions and dashboard.

---

## ✨ Main Features

### 🔐 Authentication & Authorization
- User registration and login with hashed passwords (Werkzeug)
- Session-based authentication
- Role-Based Access Control (RBAC) with decorators (`@login_required`, `@role_required`)

### 🌴 Destinations Management
- Browse popular travel destinations
- CRUD operations (Admin only)
- Search & filtering by keyword, location, and sorting

### 🛎️ Services Management
- View travel services (flight booking, hotels, guided tours)
- CRUD operations (Admin only)

### 📬 Customer Requests
- Customers can submit service requests
- Status tracking: `pending`, `in_progress`, `completed`, `rejected`
- Admin/Employee can manage and update request statuses

### 📁 File & Document Management
- Authenticated users can upload files (PDF, DOC, DOCX, PNG, JPG, TXT — max 5 MB)
- Drag & drop support
- View, download, and delete uploaded files
- File type & size validation with proper error messages

### 📊 Project Management Platform
- **Clients Management** — Add, edit, delete clients
- **Projects** — Create, update, delete projects with:
  - Title, description, status
  - Client assignment
  - Team member assignment (many-to-many)
- **Project Statuses:** `Not Started`, `In Progress`, `Completed`, `On Hold`
- **Dashboard Statistics** — Total, In Progress, Completed, Not Started, On Hold
- **Role-based visibility** — Employees only see projects they're assigned to

### 📈 Dashboard
- Overview of relevant data per role
- Quick access to features based on permissions
- Real-time statistics for projects

---

## 🛠️ Technologies Used

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | SQLite 3 |
| **Authentication** | Flask Session + Werkzeug Security |
| **CORS** | Flask-CORS |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+) |
| **Icons** | Font Awesome 6 |
| **Fonts** | Google Fonts (Inter, Poppins) |

---

## 📁 Project Structure
Shahd_Fathy/
├── app.py # Flask application (all routes & APIs)
├── database.db # SQLite database (auto-created)
├── requirements.txt # Python dependencies
├── README.md # This file
├── .gitignore # Git ignore rules
│
├── uploads/ # User-uploaded files
│ └── .gitkeep
│
├── style.css # Shared styles
│
├── index.html # Home page (destinations, services, contact)
├── login.html # Login page
├── register.html # Registration page
├── dashboard.html # User dashboard (role-based)
├── my_requests.html # Customer service requests
├── my_files.html # File upload & management
│
├── admin.html # Admin: destinations management
├── admin_services.html # Admin: services management
├── admin_requests.html # Admin: customer requests management
├── admin_users.html # Admin: users & roles management
├── admin_projects.html # Admin: projects dashboard & list
└── project_details.html # Project details + team management


---

## 🗄️ Database Schema

### Tables

| Table | Purpose |
|---|---|
| `users` | User accounts with roles |
| `destinations` | Travel destinations |
| `services` | Company services |
| `inquiries` | Contact form submissions |
| `service_requests` | Customer service requests |
| `user_files` | Uploaded files metadata |
| `clients` | Project clients |
| `projects` | Projects with status & client |
| `project_members` | Many-to-many: projects ↔ users |

### Key Relationships
- `projects.client_id` → `clients.id`
- `projects.created_by` → `users.id`
- `project_members.project_id` → `projects.id`
- `project_members.user_id` → `users.id`
- `service_requests.user_id` → `users.id`
- `user_files.user_id` → `users.id`

---

## 🔑 Roles & Permissions

| Feature | Admin | Employee | Customer |
|---|---|---|---|
| View destinations | ✅ | ✅ | ✅ |
| Manage destinations | ✅ | ❌ | ❌ |
| Manage services | ✅ | ❌ | ❌ |
| Submit requests | ✅ | ✅ | ✅ |
| Manage all requests | ✅ | ✅ | ❌ |
| View own requests | ✅ | ✅ | ✅ |
| Upload files | ✅ | ✅ | ✅ |
| Manage users | ✅ | ❌ | ❌ |
| View all projects | ✅ | ❌ | ❌ |
| View assigned projects | ✅ | ✅ | ❌ |
| Create/Delete projects | ✅ | ❌ | ❌ |
| Update project status | ✅ | ✅ (assigned only) | ❌ |
| Assign team members | ✅ | ❌ | ❌ |

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register` | Register new user |
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/check-auth` | Check authentication status |
| GET | `/api/user/profile` | Get user profile |
| PUT | `/api/user/update` | Update profile |

### Destinations
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/destinations` | List all destinations |
| GET | `/api/destinations/search` | Search & filter |
| POST | `/api/destinations` | Create (Admin) |
| PUT | `/api/destinations/<id>` | Update (Admin) |
| DELETE | `/api/destinations/<id>` | Delete (Admin) |

### Services
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/services` | List services |
| POST | `/api/services` | Create (Admin) |
| PUT | `/api/services/<id>` | Update (Admin) |
| DELETE | `/api/services/<id>` | Delete (Admin) |

### Contact & Requests
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/contact` | Submit contact form |
| POST | `/api/requests` | Create request |
| GET | `/api/requests/my` | Get own requests |
| GET | `/api/admin/requests` | Get all (Admin/Employee) |
| PUT | `/api/admin/requests/<id>` | Update status |

### Files
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/files/upload` | Upload file |
| GET | `/api/files/my` | List own files |
| DELETE | `/api/files/<id>` | Delete file |
| GET | `/uploads/<filename>` | Serve file |

### Users (Admin)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/users` | List all users |
| PUT | `/api/admin/users/<id>/role` | Update role |
| GET | `/api/users/list` | List admin/employee users |

### Clients (Admin/Employee)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/clients` | List clients |
| POST | `/api/clients` | Create (Admin) |
| PUT | `/api/clients/<id>` | Update (Admin) |
| DELETE | `/api/clients/<id>` | Delete (Admin) |

### Projects
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects` | List projects (role-filtered) |
| GET | `/api/projects/<id>` | Get details |
| POST | `/api/projects` | Create (Admin) |
| PUT | `/api/projects/<id>` | Update |
| DELETE | `/api/projects/<id>` | Delete (Admin) |
| GET | `/api/projects/stats` | Dashboard stats |
| POST | `/api/projects/<id>/members` | Add member (Admin) |
| DELETE | `/api/projects/<id>/members/<user_id>` | Remove member (Admin) |

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.8+** — [Download](https://www.python.org/downloads/)
- **pip** (comes with Python)
- Modern web browser (Chrome, Edge, Firefox)

### Step 1: Clone or Extract
```bash
cd path/to/Shahd_Fathy

### Step 2: Create Virtual Environment (Recommended)
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

### Step 3: Install Dependencies
pip install -r requirements.txt
#or manually:
pip install Flask Flask-Cors Werkzeug

### Step 4: Run the Application
python app.py

## 🎮 How to Run the Project

### Step 1: Open the App
Navigate to: **http://127.0.0.1:5001/**

### Step 2: Login Credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@wanderlust.com` | `admin123` |
| **Employee** | `employee@wanderlust.com` | `employee123` |
| **Customer** | Register a new account | — |

### Step 3: Explore Features

#### As Admin:
1. Go to **Dashboard** → see admin menu
2. Manage **Destinations** (`admin.html`)
3. Manage **Services** (`admin_services.html`)
4. Manage **Requests** (`admin_requests.html`)
5. Manage **Users & Roles** (`admin_users.html`)
6. Manage **Projects** (`admin_projects.html`)

#### As Employee:
1. Login → see Employee dashboard
2. View & manage assigned **Projects**
3. Update project **status**
4. Manage **Customer Requests**

#### As Customer:
1. Register a new account
2. Browse **Destinations** & **Services**
3. Submit a **Service Request** (`my_requests.html`)
4. Upload **Files** (`my_files.html`)
5. Update **Profile** in Dashboard

## 🧪 Testing Scenarios

### Test 1: RBAC — Employee cannot create destination
```javascript
// Login as Employee, then run in browser console:
fetch('http://127.0.0.1:5001/api/destinations', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    credentials: 'include',
    body: JSON.stringify({title:'X', description:'X', image_url:'x.jpg'})
}).then(r => r.json()).then(console.log)

// Expected: 403 Forbidden

Test 2: Search & Filter
Open index.html → use search box → verify results come from backend.

Test 3: File Upload
Login → My Files → Upload a PDF → verify it appears in list + in uploads/ folder.

Test 4: Project Assignment
Admin → Projects → create project → assign Employee → Employee logs in → sees project.

## 📝 Notes

- The database (`database.db`) is auto-created on first run with seed data:
  - 3 default destinations (Paris, Dubai, Cairo)
  - 3 default services (Flight, Hotel, Tours)
  - 3 default clients (Acme, Globex, Initech)
  - 2 default users (Admin & Employee)
- Uploaded files are stored in the `uploads/` folder with UUID names.
- Sessions use Flask's default cookie-based storage.
- The app runs on port `5001` to avoid conflicts with port `5000`.

## 🔮 Future Enhancements

- [ ] Project deadlines & milestones
- [ ] Task checklist within projects
- [ ] Comments & activity log per project
- [ ] Email notifications for status changes
- [ ] Drag & drop Kanban board for projects
- [ ] Export project reports as PDF
- [ ] Two-factor authentication
- [ ] File preview in browser
- [ ] Dark mode toggle

## 👩‍💻 Author

**Shahd Fathy Mohamed**  
Full-Stack Development Track — Voltix  
Final Project

📄 License
This project is created for educational purposes as part of the Full-Stack Development Track at Voltix.



