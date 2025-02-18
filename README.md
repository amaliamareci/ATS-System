# Recruiting Management System

A comprehensive recruiting and applicant tracking system built with Django, designed to streamline the hiring process and manage candidate pipelines effectively.

## Features

### 1. Pipeline Management
- Customizable hiring stages and sub-statuses
- Visual pipeline view with drag-and-drop functionality
- Stage-specific actions and notifications
- Automated status updates

### 2. Candidate Management
- Detailed candidate profiles
- Resume parsing and storage
- Skills and competency tracking
- Language proficiency tracking
- Professional experience management
- Certifications tracking

### 3. Position Management
- Detailed job descriptions
- Required skills and qualifications
- Benefits and perks tracking
- Multiple positions per client
- Position status tracking

### 4. Client Management
- Client organization profiles
- Custom pipeline configuration per client
- Multiple positions per client
- Client contact management

### 5. Interview Management
- Interview scheduling
- Assessment scoring
- Feedback collection
- Interview history tracking
- Calendar integration

### 6. Communication Tools
- Internal notes and comments
- Email integration
- Automated notifications
- Communication history

### 7. Document Management
- Resume storage and parsing
- Cover letter management
- Attachment handling
- Document version control

## Technical Stack

- **Backend**: Django 4.x
- **Frontend**: TailwindCSS, JavaScript
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Django built-in auth
- **File Storage**: Django FileField with AWS S3 support

## Setup Instructions

1. Clone the repository:
```bash
git clone [repository-url]
cd recruiting
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory with the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Development Guidelines

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use meaningful variable and function names
   - Add docstrings for classes and functions
   - Comment complex logic

2. **Git Workflow**
   - Create feature branches from `develop`
   - Use meaningful commit messages
   - Submit pull requests for review
   - Keep commits atomic and focused

3. **Testing**
   - Write unit tests for new features
   - Ensure all tests pass before committing
   - Maintain minimum 80% code coverage

## Deployment

The application is designed to be deployed on any Python-compatible hosting platform. Recommended platforms:

- Heroku
- DigitalOcean
- AWS Elastic Beanstalk
- Google Cloud Platform

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django Framework
- TailwindCSS
- All contributors and maintainers 