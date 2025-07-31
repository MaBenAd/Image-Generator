# Text to Image Generator

A Django web application that generates images from text prompts using the Stability AI API.

## Features

- **AI Image Generation**: Create images from text descriptions using Stable Diffusion XL
- **User Authentication**: Secure user registration and login system
- **Personal Gallery**: View and manage your generated images
- **Modern UI**: Beautiful, responsive interface with Catppuccin theme
- **Error Handling**: Comprehensive error handling and user feedback
- **Security**: CSRF protection, input validation, and SQL injection prevention

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd text2image
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export STABILITY_API_KEY="your-stability-api-key-here"
   ```

4. **Run migrations**
   ```bash
   python3 manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python3 manage.py runserver
   ```

6. **Visit the application**
   Open your browser and go to `http://localhost:8000`

## Testing & Quality

### Running Tests

**Basic test run:**
```bash
python3 manage.py test
```

**Verbose test run:**
```bash
python3 manage.py test -v 2
```

**Using the test script:**
```bash
./run_tests.sh
```

**With coverage:**
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Coverage

The application includes comprehensive tests covering:

- **Model Tests**: Database operations and model validation
- **View Tests**: HTTP requests, authentication, and error handling
- **API Integration Tests**: External API calls and error scenarios
- **Form Validation Tests**: Input validation and security
- **Security Tests**: CSRF protection and SQL injection prevention
- **Error Handling Tests**: Custom exception handling and user feedback

### Test Categories

1. **Unit Tests** (`@pytest.mark.unit`)
   - Model creation and validation
   - Form validation
   - Utility functions

2. **Integration Tests** (`@pytest.mark.integration`)
   - API integration
   - Database operations
   - Authentication flow

3. **Security Tests**
   - CSRF protection
   - Input validation
   - SQL injection prevention

## Error Handling

The application implements comprehensive error handling:

### API Errors
- **401 Unauthorized**: Invalid API key
- **403 Forbidden**: API access denied
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Service unavailable
- **Timeout**: Network timeout handling
- **Connection Errors**: Network connectivity issues

### User Input Validation
- **Empty prompts**: Rejected with clear error message
- **Too short prompts**: Minimum 3 characters required
- **Too long prompts**: Maximum 1000 characters
- **Harmful content**: Filtered for inappropriate content

### User Feedback
- **Success messages**: Confirmation of successful operations
- **Error messages**: Clear explanation of what went wrong
- **Validation errors**: Specific feedback on form issues
- **Loading states**: Visual feedback during API calls

## Security Features

- **Authentication**: Login required for image generation
- **CSRF Protection**: All forms protected against CSRF attacks
- **Input Validation**: Comprehensive prompt validation
- **SQL Injection Prevention**: Parameterized queries
- **User Isolation**: Users can only access their own images
- **Secure Headers**: Proper HTTP security headers

## API Configuration

The application uses the Stability AI API for image generation:

- **Model**: Stable Diffusion XL 1024
- **Image Size**: 1024x1024 pixels
- **Quality**: High-quality generation with 30 steps
- **Rate Limiting**: Built-in timeout and retry logic

## Development

### Project Structure
```
text2image/
├── generator/           # Main Django app
│   ├── models.py       # Database models
│   ├── views.py        # View logic with error handling
│   ├── tests.py        # Comprehensive test suite
│   └── templates/      # HTML templates
├── text2image/         # Django project settings
├── media/              # Generated images storage
├── requirements.txt    # Python dependencies
├── pytest.ini         # Test configuration
└── run_tests.sh       # Test runner script
```

### Adding New Tests

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **Security Tests**: Test security vulnerabilities
4. **Error Tests**: Test error handling scenarios

Example test structure:
```python
class MyFeatureTest(TestCase):
    def setUp(self):
        # Setup test data
        
    def test_feature_works(self):
        # Test normal operation
        
    def test_feature_handles_error(self):
        # Test error handling
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Configure proper database (PostgreSQL recommended)
- [ ] Set up static file serving
- [ ] Configure HTTPS
- [ ] Set up proper logging
- [ ] Configure environment variables
- [ ] Set up monitoring and error tracking

### Environment Variables

```bash
STABILITY_API_KEY=your-api-key-here
SECRET_KEY=your-django-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```
