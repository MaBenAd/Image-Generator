from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import tempfile
import os
from .models import Generation
from .views import generate_image_from_prompt
import requests


class GenerationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a temporary image file for testing
        self.temp_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        self.temp_image.write(b'fake image data')
        self.temp_image.close()

    def tearDown(self):
        # Clean up temporary file
        os.unlink(self.temp_image.name)

    def test_generation_creation(self):
        """Test creating a Generation instance"""
        generation = Generation.objects.create(
            user=self.user,
            prompt="A beautiful sunset",
            image=self.temp_image.name
        )
        
        self.assertEqual(generation.prompt, "A beautiful sunset")
        self.assertEqual(generation.user, self.user)
        self.assertIsNotNone(generation.created_at)
        self.assertEqual(str(generation), f"A beautiful sunset ({generation.created_at:%Y-%m-%d %H:%M})")

    def test_generation_without_user(self):
        """Test creating a Generation without a user (for backward compatibility)"""
        generation = Generation.objects.create(
            prompt="A beautiful sunset",
            image=self.temp_image.name
        )
        
        self.assertIsNone(generation.user)
        self.assertEqual(generation.prompt, "A beautiful sunset")


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_register_view(self):
        """Test user registration"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_view(self):
        """Test user login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful login

    def test_logout_view(self):
        """Test custom logout view"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Test logout
        response = self.client.get(reverse('logout'))
        
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        self.assertIn('/accounts/login/', response.url)  # Should redirect to login
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_protected_views_require_login(self):
        """Test that protected views redirect to login when not authenticated"""
        views_to_test = [
            reverse('user_gallery')
        ]
        
        for url in views_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Should redirect to login


class GenerateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_generate_view_get_authenticated(self):
        """Test GET request to generate view when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('generate'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Image')

    def test_generate_view_get_unauthenticated(self):
        """Test GET request to generate view when not authenticated"""
        response = self.client.get(reverse('generate'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    @patch('generator.views.generate_image_from_prompt')
    def test_generate_view_post_success(self, mock_generate):
        """Test successful image generation"""
        # Mock the image generation to return fake image data
        mock_generate.return_value = b'fake image data'
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('generate'), {
            'prompt': 'A beautiful sunset'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to result page
        self.assertTrue(Generation.objects.filter(prompt='A beautiful sunset').exists())

    @patch('generator.views.generate_image_from_prompt')
    def test_generate_view_post_api_error(self, mock_generate):
        """Test handling of API errors during image generation"""
        # Mock the image generation to raise an exception
        from .views import ImageGenerationError
        mock_generate.side_effect = ImageGenerationError("API Error")
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('generate'), {
            'prompt': 'A beautiful sunset'
        })
        
        # Should handle the error gracefully and return 200 with error message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generation failed')


class GalleryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create some test generations
        self.temp_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        self.temp_image.write(b'fake image data')
        self.temp_image.close()
        
        self.generation1 = Generation.objects.create(
            user=self.user,
            prompt="First image",
            image=self.temp_image.name
        )
        self.generation2 = Generation.objects.create(
            user=self.user,
            prompt="Second image",
            image=self.temp_image.name
        )

    def tearDown(self):
        os.unlink(self.temp_image.name)

    def test_gallery_view_authenticated(self):
        """Test gallery view when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('user_gallery'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Gallery')
        self.assertContains(response, 'First image')
        self.assertContains(response, 'Second image')

    def test_gallery_view_unauthenticated(self):
        """Test gallery view when not authenticated"""
        response = self.client.get(reverse('user_gallery'))
        
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_gallery_view_empty(self):
        """Test gallery view when user has no images"""
        new_user = User.objects.create_user(
            username='newuser',
            password='newpass123'
        )
        self.client.login(username='newuser', password='newpass123')
        response = self.client.get(reverse('user_gallery'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Gallery is Empty')


class ResultViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a test generation
        self.temp_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        self.temp_image.write(b'fake image data')
        self.temp_image.close()
        
        self.generation = Generation.objects.create(
            user=self.user,
            prompt="Test prompt",
            image=self.temp_image.name
        )

    def tearDown(self):
        os.unlink(self.temp_image.name)

    def test_result_view_authenticated_owner(self):
        """Test result view when authenticated user owns the generation"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('generation_result', kwargs={'pk': self.generation.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test prompt')

    def test_result_view_authenticated_not_owner(self):
        """Test result view when authenticated user doesn't own the generation"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(reverse('generation_result', kwargs={'pk': self.generation.pk}))
        
        self.assertEqual(response.status_code, 404)  # Should not be accessible

    def test_result_view_unauthenticated(self):
        """Test result view when not authenticated"""
        response = self.client.get(reverse('generation_result', kwargs={'pk': self.generation.pk}))
        
        self.assertEqual(response.status_code, 302)  # Should redirect to login


class APIIntegrationTest(TestCase):
    @patch('generator.views.requests.post')
    def test_generate_image_from_prompt_success(self, mock_post):
        """Test successful API call to Stability AI"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artifacts": [{"base64": "ZmFrZSBpbWFnZSBkYXRh"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test the function
        result = generate_image_from_prompt("A beautiful sunset")
        
        self.assertEqual(result, b'fake image data')
        mock_post.assert_called_once()

    @patch('generator.views.requests.post')
    def test_generate_image_from_prompt_api_error(self, mock_post):
        """Test API error handling"""
        # Mock API error
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        # Test that the function raises the exception
        from .views import ImageGenerationError
        with self.assertRaises(ImageGenerationError):
            generate_image_from_prompt("A beautiful sunset")

    @patch('generator.views.requests.post')
    def test_generate_image_from_prompt_http_error(self, mock_post):
        """Test HTTP error handling"""
        # Mock HTTP error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        # Test that the function raises the exception
        from .views import ImageGenerationError
        with self.assertRaises(ImageGenerationError):
            generate_image_from_prompt("A beautiful sunset")


class FormValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_empty_prompt_validation(self):
        """Test that empty prompts are rejected"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('generate'), {
            'prompt': ''
        })
        
        # Should stay on the same page (no redirect)
        self.assertEqual(response.status_code, 200)

    def test_very_long_prompt_validation(self):
        """Test that very long prompts are handled properly"""
        long_prompt = "A" * 1000  # Very long prompt
        self.client.login(username='testuser', password='testpass123')
        
        with patch('generator.views.generate_image_from_prompt') as mock_generate:
            mock_generate.return_value = b'fake image data'
            response = self.client.post(reverse('generate'), {
                'prompt': long_prompt
            })
        
        # Should handle long prompts gracefully
        self.assertEqual(response.status_code, 302)


class SecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_csrf_protection(self):
        """Test that CSRF protection is working"""
        # Create a client without CSRF
        client_no_csrf = Client(enforce_csrf_checks=True)
        client_no_csrf.login(username='testuser', password='testpass123')
        
        response = client_no_csrf.post(reverse('generate'), {
            'prompt': 'Test prompt'
        })
        
        # Should be rejected due to missing CSRF token
        self.assertEqual(response.status_code, 403)

    def test_sql_injection_protection(self):
        """Test that SQL injection attempts are handled safely"""
        malicious_prompt = "'; DROP TABLE generator_generation; --"
        self.client.login(username='testuser', password='testpass123')
        
        with patch('generator.views.generate_image_from_prompt') as mock_generate:
            mock_generate.return_value = b'fake image data'
            response = self.client.post(reverse('generate'), {
                'prompt': malicious_prompt
            })
        
        # Should handle malicious input safely
        self.assertEqual(response.status_code, 302)
        # Check that the prompt was saved as-is (not executed as SQL)
        generation = Generation.objects.filter(prompt=malicious_prompt).first()
        self.assertIsNotNone(generation)


class ErrorHandlingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_invalid_prompt_validation(self):
        """Test validation of invalid prompts"""
        from .views import validate_prompt
        
        # Test empty prompt
        with self.assertRaises(Exception):
            validate_prompt("")
        
        # Test too short prompt
        with self.assertRaises(Exception):
            validate_prompt("ab")
        
        # Test too long prompt
        with self.assertRaises(Exception):
            validate_prompt("a" * 1001)
        
        # Test harmful content
        with self.assertRaises(Exception):
            validate_prompt("hack the system")

    def test_valid_prompt_validation(self):
        """Test validation of valid prompts"""
        from .views import validate_prompt
        
        # Test valid prompt
        result = validate_prompt("A beautiful sunset")
        self.assertEqual(result, "A beautiful sunset")
        
        # Test prompt with extra whitespace
        result = validate_prompt("  A beautiful sunset  ")
        self.assertEqual(result, "A beautiful sunset")
