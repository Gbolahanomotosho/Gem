"""
AI Provider Manager for Gem AI
Supports: OpenAI, Gemini, Grok, Anthropic, Groq, and more
ULTRA FIXED VERSION - Groq now works perfectly with detailed logging
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
                logger.info(f"🔑 Detected AI provider: {provider_name}")
                self._initialize_client()
                return
        
        logger.error("❌ No AI provider API key found in environment variables")
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
                # ULTRA FIXED: Groq initialization with multiple fallback methods
                logger.info("🔧 Initializing Groq client...")
                try:
                    from groq import Groq
                    # Method 1: Try basic initialization
                    self.client = Groq(api_key=self.api_key)
                    logger.info("✅ Groq client initialized (Method 1: Basic)")
                except TypeError as te:
                    logger.warning(f"⚠️ Groq Method 1 failed: {te}")
                    try:
                        # Method 2: Try with custom HTTP client
                        from groq import Groq
                        import httpx
                        http_client = httpx.Client(
                            timeout=60.0,
                            follow_redirects=True
                        )
                        self.client = Groq(
                            api_key=self.api_key,
                            http_client=http_client
                        )
                        logger.info("✅ Groq client initialized (Method 2: Custom HTTP)")
                    except Exception as e2:
                        logger.error(f"⚠️ Groq Method 2 failed: {e2}")
                        # Method 3: Use direct API wrapper
                        self.client = self._create_groq_direct_api(self.api_key)
                        logger.info("✅ Groq client initialized (Method 3: Direct API)")
                
            elif self.active_provider == 'cohere':
                import cohere
                self.client = cohere.Client(self.api_key)
                
            elif self.active_provider == 'huggingface':
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(token=self.api_key)
                
            logger.info(f"✅ Successfully initialized {self.active_provider} client")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import {self.active_provider} library: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.active_provider}: {e}")
            raise
    
    def _create_groq_direct_api(self, api_key: str):
        """Create a direct API wrapper for Groq when SDK fails"""
        class GroqDirectAPI:
            def __init__(self, api_key):
                self.api_key = api_key
                self.base_url = "https://api.groq.com/openai/v1"
                logger.info("🔧 Using Groq Direct API wrapper")
            
            class Chat:
                def __init__(self, parent):
                    self.parent = parent
                
                class Completions:
                    def __init__(self, parent):
                        self.parent = parent
                    
                    def create(self, model, messages, temperature=0.3, max_tokens=2000, **kwargs):
                        """Make direct API call to Groq"""
                        import requests
                        import json
                        
                        logger.info(f"📡 Making direct Groq API call...")
                        logger.info(f"📝 Model: {model}")
                        logger.info(f"📝 Messages: {len(messages)} message(s)")
                        
                        headers = {
                            "Authorization": f"Bearer {self.parent.parent.api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        data = {
                            "model": model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        }
                        
                        try:
                            response = requests.post(
                                f"{self.parent.parent.base_url}/chat/completions",
                                headers=headers,
                                json=data,
                                timeout=120
                            )
                            
                            logger.info(f"📡 Groq API Response Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                result = response.json()
                                logger.info(f"✅ Groq API call successful!")
                                
                                # Create response object that matches Groq SDK format
                                class Message:
                                    def __init__(self, content):
                                        self.content = content
                                
                                class Choice:
                                    def __init__(self, message_content):
                                        self.message = Message(message_content)
                                
                                class Response:
                                    def __init__(self, content):
                                        self.choices = [Choice(content)]
                                
                                return Response(result['choices'][0]['message']['content'])
                            else:
                                error_msg = f"Groq API error: {response.status_code} - {response.text}"
                                logger.error(f"❌ {error_msg}")
                                raise Exception(error_msg)
                                
                        except requests.exceptions.RequestException as e:
                            logger.error(f"❌ Groq API request failed: {e}")
                            raise
                
                def __init__(self, parent):
                    self.parent = parent
                    self.completions = self.Completions(self)
            
            def __init__(self, api_key):
                self.api_key = api_key
                self.base_url = "https://api.groq.com/openai/v1"
                self.chat = self.Chat(self)
        
        return GroqDirectAPI(api_key)
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """Generate completion using the active AI provider"""
        
        logger.info("="*80)
        logger.info(f"🤖 Generating AI completion with {self.active_provider}")
        logger.info(f"📝 Prompt length: {len(prompt)} characters")
        logger.info(f"🎛️ Temperature: {temperature}, Max tokens: {max_tokens}")
        
        try:
            if self.active_provider == 'openai':
                response = self.client.ChatCompletion.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response['choices'][0]['message']['content']
                logger.info(f"✅ OpenAI completion successful ({len(result)} chars)")
                return result
            
            elif self.active_provider == 'gemini':
                model = self.client.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-pro'))
                response = model.generate_content(prompt)
                result = response.text
                logger.info(f"✅ Gemini completion successful ({len(result)} chars)")
                return result
            
            elif self.active_provider == 'anthropic':
                message = self.client.messages.create(
                    model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = message.content[0].text
                logger.info(f"✅ Anthropic completion successful ({len(result)} chars)")
                return result
            
            elif self.active_provider == 'grok':
                response = self.client.ChatCompletion.create(
                    model=os.getenv('GROK_MODEL', 'grok-beta'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result = response['choices'][0]['message']['content']
                logger.info(f"✅ Grok completion successful ({len(result)} chars)")
                return result
            
            elif self.active_provider == 'groq':
                # ULTRA FIXED: Comprehensive Groq handling with detailed logging
                model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
                messages = [{"role": "user", "content": prompt}]
                
                logger.info(f"🚀 Calling Groq API with model: {model}")
                
                try:
                    # Try native Groq SDK client
                    if hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
                        logger.info("📡 Using Groq SDK client...")
                        response = self.client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        result = response.choices[0].message.content
                        logger.info(f"✅ Groq SDK completion successful ({len(result)} chars)")
                        logger.info(f"📄 Response preview: {result[:200]}...")
                        return result
                    else:
                        # This shouldn't happen with our direct API wrapper, but just in case
                        logger.warning("⚠️ Groq client structure unexpected, using direct method")
                        raise AttributeError("Unexpected client structure")
                        
                except Exception as e:
                    logger.error(f"❌ Groq completion error: {type(e).__name__}: {e}")
                    logger.error(f"❌ Full error: {str(e)}")
                    raise  # Re-raise the exception so we can see it in the logs
            
            elif self.active_provider == 'cohere':
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                result = response.generations[0].text
                logger.info(f"✅ Cohere completion successful ({len(result)} chars)")
                return result
            
            elif self.active_provider == 'huggingface':
                response = self.client.text_generation(
                    prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature
                )
                logger.info(f"✅ HuggingFace completion successful ({len(response)} chars)")
                return response
            
        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌❌❌ AI GENERATION COMPLETELY FAILED ❌❌❌")
            logger.error(f"❌ Provider: {self.active_provider}")
            logger.error(f"❌ Error Type: {type(e).__name__}")
            logger.error(f"❌ Error Message: {str(e)}")
            logger.error("="*80)
            raise  # Re-raise so the calling function knows it failed
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the active provider"""
        return {
            'provider': self.active_provider,
            'has_api_key': bool(self.api_key),
            'is_initialized': bool(self.client)
        }
