from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from .models import Generation
from django.core.files.base import ContentFile
from io import BytesIO
import requests
import base64
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
# Only raise error in production or if explicitly required
if not STABILITY_API_KEY and os.environ.get("REQUIRE_STABILITY_API", "false").lower() == "true":
    raise RuntimeError("STABILITY_API_KEY environment variable not set.")


class ImageGenerationError(Exception):
    """Custom exception for image generation errors"""
    pass


def validate_prompt(prompt):
    """Validate the prompt before sending to API"""
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt cannot be empty")
    
    if len(prompt.strip()) < 3:
        raise ValidationError("Prompt must be at least 3 characters long")
    
    if len(prompt) > 1000:
        raise ValidationError("Prompt is too long (maximum 1000 characters)")
    
    # Check for potentially harmful content
    harmful_words = ['hack', 'exploit', 'virus', 'malware', 'spam']
    prompt_lower = prompt.lower()
    for word in harmful_words:
        if word in prompt_lower:
            raise ValidationError("Prompt contains inappropriate content")
    
    return prompt.strip()


# Calls Stability AI API to generate an image from a prompt
def generate_image_from_prompt(prompt):
    """Generate image from prompt with comprehensive error handling"""
    try:
        # Validate prompt
        validated_prompt = validate_prompt(prompt)
        
        # Check if API key is available
        if not STABILITY_API_KEY:
            raise ImageGenerationError("Stability AI API key not configured. Please set STABILITY_API_KEY environment variable.")
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "text_prompts": [{"text": validated_prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        # Make API request with timeout
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        # Handle different HTTP status codes
        if response.status_code == 401:
            raise ImageGenerationError("Invalid API key. Please check your configuration.")
        elif response.status_code == 403:
            raise ImageGenerationError("API access denied. Please check your account status.")
        elif response.status_code == 429:
            raise ImageGenerationError("Rate limit exceeded. Please try again later.")
        elif response.status_code == 500:
            raise ImageGenerationError("Stability AI service is currently unavailable. Please try again later.")
        elif response.status_code != 200:
            raise ImageGenerationError(f"API error: {response.status_code} - {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # Validate response structure
        if "artifacts" not in data or not data["artifacts"]:
            raise ImageGenerationError("Invalid response from API")
        
        # The API returns base64-encoded images
        image_b64 = data["artifacts"][0]["base64"]
        if not image_b64:
            raise ImageGenerationError("No image data received from API")
        
        image_data = base64.b64decode(image_b64)
        return image_data
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while generating image for prompt: {prompt[:50]}...")
        raise ImageGenerationError("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while generating image for prompt: {prompt[:50]}...")
        raise ImageGenerationError("Network connection error. Please check your internet connection.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while generating image: {str(e)}")
        raise ImageGenerationError(f"Network error: {str(e)}")
    except ValidationError as e:
        logger.warning(f"Validation error for prompt: {prompt[:50]}... - {str(e)}")
        raise ImageGenerationError(str(e))
    except Exception as e:
        logger.error(f"Unexpected error while generating image: {str(e)}")
        raise ImageGenerationError("An unexpected error occurred. Please try again.")


@login_required
def generate(request):
    """Handle image generation with error handling"""
    if request.method == "POST":
        try:
            prompt = request.POST.get("prompt", "").strip()
            
            # Generate image
            image_data = generate_image_from_prompt(prompt)
            
            # Create file and save to database
            image_file = ContentFile(image_data, name="generated.png")
            generation = Generation.objects.create(
                prompt=prompt, 
                image=image_file, 
                user=request.user
            )
            
            messages.success(request, "Image generated successfully!")
            return redirect("generation_result", pk=generation.pk)
            
        except ImageGenerationError as e:
            messages.error(request, f"Generation failed: {str(e)}")
            return render(request, "generator/generate.html", {"error": str(e), "prompt": prompt})
        except Exception as e:
            logger.error(f"Unexpected error in generate view: {str(e)}")
            messages.error(request, "An unexpected error occurred. Please try again.")
            return render(request, "generator/generate.html", {"error": "An unexpected error occurred"})
    
    return render(request, "generator/generate.html")


@login_required
def generation_result(request, pk):
    """Display generation result with error handling"""
    try:
        generation = Generation.objects.get(pk=pk, user=request.user)
        return render(request, "generator/result.html", {"generation": generation})
    except Generation.DoesNotExist:
        raise Http404("Generation not found or you don't have permission to view it.")


@login_required
def user_gallery(request):
    """Display user's gallery with error handling"""
    try:
        generations = Generation.objects.filter(user=request.user).order_by('-created_at')
        return render(request, "generator/gallery.html", {"generations": generations})
    except Exception as e:
        logger.error(f"Error loading gallery for user {request.user.username}: {str(e)}")
        messages.error(request, "Error loading your gallery. Please try again.")
        return render(request, "generator/gallery.html", {"generations": []})


def register(request):
    """Handle user registration with error handling"""
    if request.method == "POST":
        try:
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, f"Welcome, {user.username}! Your account has been created successfully.")
                return redirect("generate")
            else:
                # Display form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            messages.error(request, "An error occurred during registration. Please try again.")
    else:
        form = UserCreationForm()
    
    return render(request, "generator/register.html", {"form": form})


def login_view(request):
    """Handle user login with error handling"""
    if request.method == "POST":
        try:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f"Welcome back, {username}!")
                    return redirect("generate")
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            messages.error(request, "An error occurred during login. Please try again.")
    else:
        form = AuthenticationForm()
    
    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    """Custom logout view that handles GET requests"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect("login")
