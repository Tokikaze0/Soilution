# Soilution - Smart Soil Analysis & Crop Recommendation System

A Django-based web application that provides real-time soil analysis and crop recommendations using machine learning and ESP32 sensor data.

## Features

- Real-time soil analysis from ESP32 sensors
- Machine learning-powered crop recommendations
- User authentication and authorization
- Admin dashboard for user management
- Real-time messaging system
- Google OAuth integration
- Responsive web interface

## Technology Stack

- **Backend**: Django 5.1.6
- **Database**: PostgreSQL
- **Real-time**: Django Channels with Redis
- **Machine Learning**: TensorFlow, scikit-learn
- **Authentication**: Django Allauth
- **File Storage**: Supabase
- **Production**: Gunicorn, WhiteNoise

## Prerequisites

- Python 3.10+
- PostgreSQL
- Redis (for production)
- Supabase account
- Google OAuth credentials

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd soilution_v2
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp deployment.env.example .env
   # Edit .env with your actual values
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Security Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# CSRF Settings
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://your-domain.com

# Session Security
SESSION_COOKIE_AGE=3600
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# SSL Settings
SECURE_SSL_REDIRECT=True

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis (for channels)
REDIS_URL=redis://localhost:6379

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Supabase Settings
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## Deployment

### Heroku Deployment

1. **Install Heroku CLI**
2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Add PostgreSQL addon**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. **Add Redis addon**
   ```bash
   heroku addons:create heroku-redis:hobby-dev
   ```

6. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   # Add all other environment variables
   ```

7. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

8. **Run migrations**
   ```bash
   heroku run python manage.py migrate
   ```

9. **Create superuser**
   ```bash
   heroku run python manage.py createsuperuser
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t soilution .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 soilution
   ```

### Manual Server Deployment

1. **Set up your server** (Ubuntu/Debian recommended)
2. **Install dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip postgresql redis-server nginx
   ```

3. **Clone and set up the application**
   ```bash
   git clone <repository-url>
   cd soilution_v2
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp deployment.env.example .env
   # Edit .env with your actual values
   ```

5. **Run deployment script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

6. **Set up Gunicorn service**
   ```bash
   sudo nano /etc/systemd/system/soilution.service
   ```

   Add the following content:
   ```ini
   [Unit]
   Description=Soilution Django Application
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/soilution_v2
   Environment="PATH=/path/to/soilution_v2/venv/bin"
   ExecStart=/path/to/soilution_v2/venv/bin/gunicorn --workers 3 --bind unix:/path/to/soilution_v2/soilution.sock soilution.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start the service**
   ```bash
   sudo systemctl start soilution
   sudo systemctl enable soilution
   ```

8. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/soilution
   ```

   Add the following configuration:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location = /favicon.ico { access_log off; log_not_found off; }
       
       location /static/ {
           root /path/to/soilution_v2;
       }

       location /media/ {
           root /path/to/soilution_v2;
       }

       location / {
           include proxy_params;
           proxy_pass http://unix:/path/to/soilution_v2/soilution.sock;
       }
   }
   ```

9. **Enable the site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/soilution /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## API Endpoints

### ESP32 Data API
- **POST** `/api/esp32-data/` - Receive sensor data from ESP32

### Soil Analysis API
- **POST** `/api/analyze-soil/` - Analyze soil parameters
- **GET** `/api/crop-history/` - Get crop recommendation history
- **GET** `/api/workspace-stats/` - Get workspace statistics

## Security Features

- CSRF protection enabled
- XSS protection headers
- HSTS headers
- Secure session cookies
- Input validation and sanitization
- Rate limiting on API endpoints
- Environment-based configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support, email support@soilution.com or create an issue in the repository.
