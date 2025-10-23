"""
AI Provider Manager for Gem AI
Supports: OpenAI, Gemini, Grok, Anthropic, Groq, and more
FIXED VERSION - Groq compatibility issue resolved
"""

import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AIProviderManager:
    """Manages multiple AI providers dynamically based on API keys"""
    
    PROVIDERS = {
        'OPENAI_API_KEY': 'openai',
        'GEMINI_API_KEY': 'gemini',
        'ANTHROPIC_API_KEY': 'anthropic',
        'GROK_API_KEY': 'grok',
        'GROQ_API_KEY': 'groq',
        'COHERE_API_KEY': 'cohere',
        'HUGGINGFACE_API_KEY': 'huggingface'
    }
    
    def __init__(self):
        self.active_provider = None
        self.api_key = None
        self.client = None
        self._detect_provider()
    
    def _detect_provider(self):
        """Detect which AI provider to use based on available API keys"""
        for env_var, provider_name in self.PROVIDERS.items():
            api_key = os.getenv(env_var)
            if api_key:
                self.active_provider = provider_name
                self.api_key = api_key
                logger.info(f"Detected AI provider: {provider_name}")
                self._initialize_client()
                return
        
        logger.error("No AI provider API key found in environment variables")
        raise ValueError("No AI API key found. Please set one of: " + ", ".join(self.PROVIDERS.keys()))
    
    def _initialize_client(self):
        """Initialize the appropriate AI client"""
        try:
            if self.active_provider == 'openai':
                import openai
                openai.api_key = self.api_key
                self.client = openai
                
            elif self.active_provider == 'gemini':
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
                
            elif self.active_provider == 'anthropic':
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                
            elif self.active_provider == 'grok':
                import openai  # Grok uses OpenAI-compatible API
                self.client = openai
                self.client.api_key = self.api_key
                self.client.api_base = "https://api.x.ai/v1"
                
            elif self.active_provider == 'groq':
                # FIXED: Groq initialization with proper error handling
                try:
                    from groq import Groq
                    # Try to initialize without any extra parameters that might cause issues
                    self.client = Groq(api_key=self.api_key)
                    logger.info("Groq client initialized successfully")
                except TypeError as te:
                    # If there's a TypeError, try alternative initialization
                    logger.warning(f"Groq initialization attempt 1 failed: {te}")
                    try:
                        from groq import Groq
                        # Alternative: Initialize with minimal parameters
                        import httpx
                        http_client = httpx.Client(timeout=30.0)
                        self.client = Groq(api_key=self.api_key, http_client=http_client)
                        logger.info("Groq client initialized with custom http client")
                    except Exception as e2:
                        logger.error(f"Groq initialization attempt 2 failed: {e2}")
                        # Last resort: use a simple wrapper
                        self.client = self._create_groq_wrapper(self.api_key)
                        logger.info("Using Groq wrapper fallback")
                
            elif self.active_provider == 'cohere':
                import cohere
                self.client = cohere.Client(self.api_key)
                
            elif self.active_provider == 'huggingface':
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(token=self.api_key)
                
            logger.info(f"Successfully initialized {self.active_provider} client")
            
        except ImportError as e:
            logger.error(f"Failed to import {self.active_provider} library: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize {self.active_provider}: {e}")
            raise
    
    def _create_groq_wrapper(self, api_key: str):
        """Create a simple wrapper for Groq API if direct initialization fails"""
        class GroqWrapper:
            def __init__(self, api_key):
                self.api_key = api_key
                self.base_url = "https://api.groq.com/openai/v1"
            
            def chat_completions_create(self, model, messages, temperature=0.3, max_tokens=2000):
                """Make a direct API call to Groq"""
                import requests
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Create a simple object with the expected structure
                    class Choice:
                        def __init__(self, message_content):
                            self.message = type('obj', (object,), {'content': message_content})()
                    
                    class Response:
                        def __init__(self, content):
                            self.choices = [Choice(content)]
                    
                    return Response(result['choices'][0]['message']['content'])
                else:
                    raise Exception(f"Groq API error: {response.status_code} - {response.text}")
        
        return GroqWrapper(api_key)
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """Generate completion using the active AI provider"""
        
        try:
            if self.active_provider == 'openai':
                response = self.client.ChatCompletion.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response['choices'][0]['message']['content']
            
            elif self.active_provider == 'gemini':
                model = self.client.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-pro'))
                response = model.generate_content(prompt)
                return response.text
            
            elif self.active_provider == 'anthropic':
                message = self.client.messages.create(
                    model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
            
            elif self.active_provider == 'grok':
                response = self.client.ChatCompletion.create(
                    model=os.getenv('GROK_MODEL', 'grok-beta'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response['choices'][0]['message']['content']
            
            elif self.active_provider == 'groq':
                # FIXED: Handle both native Groq client and wrapper
                model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
                messages = [{"role": "user", "content": prompt}]
                
                try:
                    # Try native Groq client first
                    if hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
                        response = self.client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        return response.choices[0].message.content
                    else:
                        # Use wrapper
                        response = self.client.chat_completions_create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Groq completion error: {e}")
                    # Fallback to wrapper
                    response = self.client.chat_completions_create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
            
            elif self.active_provider == 'cohere':
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.generations[0].text
            
            elif self.active_provider == 'huggingface':
                response = self.client.text_generation(
                    prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature
                )
                return response
            
        except Exception as e:
            logger.error(f"AI generation failed with {self.active_provider}: {str(e)}")
            raise
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the active provider"""
        return {
            'provider': self.active_provider,
            'has_api_key': bool(self.api_key),
            'is_initialized': bool(self.client)
        }
