"""
AI Provider Manager for Gem AI
Supports: OpenAI, Gemini, Grok, Anthropic, Groq, and more
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
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                
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
                response = self.client.chat.completions.create(
                    model=os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768'),
                    messages=[{"role": "user", "content": prompt}],
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
