# Qqumi API

A comprehensive Django REST Framework backend API for an educational platform with subscription-based access to premium content.

## 📖 Project Overview

Qqumi is a backend API platform designed for educational content management. The system provides:

- **Course Management**: Organize educational content into categories and courses
- **Subscription System**: Manage user subscriptions with different tariff plans
- **Access Control**: Premium content access based on active subscriptions
- **JWT Authentication**: Secure authentication and authorization
- **Comprehensive Documentation**: Auto-generated Swagger/OpenAPI documentation

## 🛠 Tech Stack

### Core Technologies
- **Python 3.12+**
- **Django 6.0.2** - Web framework
- **Django REST Framework 3.16.1** - REST API framework
- **JWT Authentication** - Secure token-based authentication

### Development & Documentation
- **drf-spectacular 0.29.0** - OpenAPI schema generation and Swagger UI
- **Pillow 12.1.1** - Image processing for media files

### Database
- **SQLite** (default for development)
- **PostgreSQL** (recommended for production)

### Dependencies Management
- **python-dotenv** - Environment variable management

## 🚀 Installation & Setup

### Prerequisites
- Python 3.12 or higher
- pip package manager

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bilimly-api
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example environment file and configure your settings:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` file with your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## ⚙️ Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (Optional - uses SQLite by default)
# POSTGRES_DB=your_db_name
# POSTGRES_USER=your_db_user
# POSTGRES_PASSWORD=your_db_password
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
```

**Important**: Never commit the `.env` file to version control.

## 👤 Creating Superuser

To access the Django Admin panel, create a superuser:

```bash
python manage.py createsuperuser
```

Follow the prompts to set:
- Username
- Email (optional)
- Password

## 📚 API Documentation

The API comes with comprehensive auto-generated documentation:

### Swagger UI (Interactive)
Access the interactive API documentation at:
```
http://127.0.0.1:8000/api/docs/
```

### Redoc (Alternative View)
Alternative documentation view available at:
```
http://127.0.0.1:8000/api/redoc/
```

### Schema Download
Download the OpenAPI schema in YAML format:
```
http://127.0.0.1:8000/api/schema/
```

## 🔐 Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Tokens) for authentication.

#### Login Endpoint
```
POST /api/users/login/
```

Request body:
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Using Bearer Token

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 💼 Business Logic

### Subscription System

- **Single Active Subscription**: Each user can have only one active subscription at a time
- **Automatic Expiration**: Subscriptions automatically expire based on the tariff duration
- **Tariff Management**: Tariffs are managed exclusively through the Django Admin panel
- **Trial Periods**: Support for trial tariffs with zero cost

### Content Access

- **Public Content**: Categories and basic course information are publicly accessible
- **Premium Content**: Full course details require an active subscription
- **Access Control**: The system automatically validates subscription status for protected content

### Data Management

- **Read-Only API**: Courses and categories are read-only via the API
- **Admin Management**: All content creation and modification happens through Django Admin
- **Media Handling**: Course images are stored in the media directory with proper URL handling

## 📄 Pagination

The API supports pagination for list endpoints:

### Parameters
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

### Example
```
GET /api/courses/?page=2&page_size=10
```

### Response Format
```json
{
    "count": 150,
    "next": "http://127.0.0.1:8000/api/courses/?page=3",
    "previous": "http://127.0.0.1:8000/api/courses/?page=1",
    "results": [...]
}
```

## 🖼️ Media Files

### Configuration

Media files (images) are handled with the following settings:

- **Media URL**: `/media/`
- **Media Root**: `./media/` directory in project root

### Storage

- Images are stored in the local filesystem
- Categories and courses can have associated images
- Media files are served during development
- For production, configure a proper media storage solution

### Accessing Images

Course/category images can be accessed via:
```
http://127.0.0.1:8000/media/categories/image.jpg
http://127.0.0.1:8000/media/courses/image.jpg
```

## 👮 Admin Panel

Access the Django Admin panel at:
```
http://127.0.0.1:8000/admin/
```

### Admin Features

- User management with role-based permissions
- Content organization and categorization
- Subscription tracking and management
- Audit trail for content changes

## 🔒 Permissions

#### Protected Operations
- Subscription creation requires authentication
- Content access is validated against active subscriptions

### Permission Classes

The API uses Django REST Framework's permission system:
- `IsAuthenticated` - Requires valid JWT token
- `IsAdminUser` - Requires admin privileges
- Custom permissions for subscription-based access

## 🧪 Development Best Practices

### Code Organization

- **Keep Views Thin**: Business logic should be in services or models, not views
- **Use Serializers**: Always use DRF serializers for data validation and serialization
- **Leverage Permissions**: Use DRF permissions for access control
- **Follow REST Conventions**: Use standard HTTP methods and status codes

### Security

- **Environment Variables**: Never commit sensitive data to version control
- **JWT Security**: Use secure token storage and proper expiration times
- **Input Validation**: Always validate user input through serializers
- **Permission Checks**: Implement proper permission checks for all endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs/`
- Review the Django Admin interface at `/admin/`

---

**Bilimly API** - Empowering education through technology