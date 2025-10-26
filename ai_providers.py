"""
AI Provider Manager for Gem AI - COMPLETE FIXED VERSION
Supports all current AI models with automatic fallback
"""

import os
from typing import Dict, Any, Optional
import logging
import requests
import json

logger = logging.getLogger(__name__)


class AIProviderManager:
    """Manages multiple AI providers with direct API calls"""
    
    PROVIDERS = {
        'OPENAI_API_KEY': 'openai',
        'GEMINI_API_KEY': 'gemini',
        'ANTHROPIC_API_KEY': 'anthropic',
        'GROK_API_KEY': 'grok',
        'GROQ_API_KEY': 'groq',
        'COHERE_API_KEY': 'cohere',
        'HUGGINGFACE_API_KEY': 'huggingface'
    }
    
    # Current supported Groq models (October 2025)
    GROQ_MODELS = [
        'llama-3.1-70b-versatile',  # RECOMMENDED - Best balance
        'llama-3.1-8b-instant',     # Fastest, lighter
        'llama3-70b-8192',          # Alternative
        'llama-3.2-90b-text-preview',  # Latest preview
        'gemma2-9b-it',             # Google Gemma
        'mixtral-8x7b-32768'        # Legacy (may not work)
    ]
    
    def __init__(self):
        self.active_provider = None
        self.api_key = None
        self.client = "direct_api"
        self.current_model = None
        self._detect_provider()
    
    def _detect_provider(self):
        """Detect which AI provider to use based on available API keys"""
        logger.info("="*80)
        logger.info("🔍 DETECTING AI PROVIDER...")
        
        for env_var, provider_name in self.PROVIDERS.items():
            api_key = os.getenv(env_var)
            if api_key:
                self.active_provider = provider_name
                self.api_key = api_key
                logger.info(f"✅ Detected AI provider: {provider_name}")
                logger.info(f"✅ API Key (first 10 chars): {api_key[:10]}...")
                logger.info(f"✅ API Key (last 4 chars): ...{api_key[-4:]}")
                logger.info("="*80)
                return
        
        logger.error("="*80)
        logger.error("❌ No AI provider API key found!")
        logger.error("="*80)
        raise ValueError("No AI API key found")
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """Generate completion using direct API calls"""
        
        logger.info("="*80)
        logger.info(f"🤖 STARTING AI COMPLETION")
        logger.info(f"🤖 Provider: {self.active_provider}")
        logger.info(f"📝 Prompt length: {len(prompt)} chars")
        logger.info(f"🎛️ Settings: temp={temperature}, max_tokens={max_tokens}")
        logger.info("="*80)
        
        try:
            if self.active_provider == 'groq':
                return self._groq_direct_api(prompt, max_tokens, temperature)
            
            elif self.active_provider == 'openai':
                return self._openai_api(prompt, max_tokens, temperature)
            
            elif self.active_provider == 'anthropic':
                return self._anthropic_api(prompt, max_tokens, temperature)
            
            else:
                raise Exception(f"Provider {self.active_provider} not implemented yet")
                
        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌ FATAL: AI Generation Failed!")
            logger.error(f"❌ Provider: {self.active_provider}")
            logger.error(f"❌ Error Type: {type(e).__name__}")
            logger.error(f"❌ Error Message: {str(e)}")
            logger.error("="*80)
            raise
    
    def _groq_direct_api(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Direct Groq API call with automatic model fallback"""
        
        logger.info("🚀 GROQ: Preparing direct API call")
        
        # Get model from environment or use recommended default
        user_model = os.getenv('GROQ_MODEL')
        
        if user_model:
            models_to_try = [user_model] + [m for m in self.GROQ_MODELS if m != user_model]
            logger.info(f"📋 GROQ: User specified model: {user_model}")
        else:
            models_to_try = self.GROQ_MODELS
            logger.info(f"📋 GROQ: No model specified, will try in order: {models_to_try}")
        
        # Try each model until one works
        last_error = None
        for model_name in models_to_try:
            try:
                logger.info(f"🔄 GROQ: Trying model: {model_name}")
                result = self._make_groq_request(model_name, prompt, max_tokens, temperature)
                self.current_model = model_name
                logger.info(f"✅ GROQ: Successfully used model: {model_name}")
                return result
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ GROQ: Model {model_name} failed: {error_msg[:100]}")
                
                # Check if it's a model decommissioned error
                if 'decommissioned' in error_msg.lower() or 'not found' in error_msg.lower():
                    logger.warning(f"⚠️ GROQ: Model {model_name} is no longer available, trying next...")
                    last_error = e
                    continue
                else:
                    # Other errors should be raised immediately
                    raise
        
        # If we get here, all models failed
        logger.error("❌ GROQ: All models failed!")
        logger.error(f"❌ GROQ: Models tried: {models_to_try}")
        raise Exception(f"All Groq models failed. Last error: {last_error}")
    
    def _make_groq_request(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Make actual HTTP request to Groq API"""
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        logger.info(f"📡 GROQ: Sending request to {url}")
        logger.info(f"📡 GROQ: Model: {model}")
        logger.info(f"📡 GROQ: Message length: {len(prompt)} chars")
        logger.info(f"📡 GROQ: Making HTTP POST request...")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        logger.info(f"📡 GROQ: Response Status: {response.status_code}")
        
        # Log response preview
        try:
            response_preview = response.text[:500]
            logger.info(f"📡 GROQ: Response preview: {response_preview}")
        except:
            logger.warning("⚠️ GROQ: Could not read response preview")
        
        if response.status_code == 200:
            logger.info("✅ GROQ: Request successful!")
            
            try:
                result_data = response.json()
                logger.info(f"✅ GROQ: JSON parsed successfully")
                logger.info(f"✅ GROQ: Response structure: {list(result_data.keys())}")
                
                if 'choices' in result_data and len(result_data['choices']) > 0:
                    content = result_data['choices'][0]['message']['content']
                    logger.info(f"✅ GROQ: Extracted content ({len(content)} chars)")
                    logger.info(f"📄 GROQ: Content preview: {content[:200]}...")
                    return content
                else:
                    logger.error(f"❌ GROQ: Unexpected response structure")
                    raise Exception("Invalid response structure from Groq API")
                    
            except json.JSONDecodeError as je:
                logger.error(f"❌ GROQ: JSON decode error: {je}")
                raise Exception(f"Failed to parse Groq response: {je}")
                
        else:
            # Non-200 status code
            error_text = response.text
            logger.error(f"❌ GROQ: API error {response.status_code}")
            logger.error(f"❌ GROQ: Error response: {error_text}")
            
            # Parse error details
            try:
                error_json = response.json()
                logger.error(f"❌ GROQ: Error details: {error_json}")
            except:
                pass
            
            raise Exception(f"Groq API error {response.status_code}: {error_text}")
    
    def _openai_api(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Direct OpenAI API call"""
        logger.info("🚀 OPENAI: Preparing API call")
        
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        logger.info(f"📡 OPENAI: Sending request with model: {model}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        logger.info(f"📡 OPENAI: Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            logger.info(f"✅ OPENAI: Success! Content length: {len(content)} chars")
            return content
        else:
            logger.error(f"❌ OPENAI: Error {response.status_code}: {response.text}")
            raise Exception(f"OpenAI API error {response.status_code}: {response.text}")
    
    def _anthropic_api(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Direct Anthropic API call"""
        logger.info("🚀 ANTHROPIC: Preparing API call")
        
        model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        logger.info(f"📡 ANTHROPIC: Sending request with model: {model}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        logger.info(f"📡 ANTHROPIC: Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            logger.info(f"✅ ANTHROPIC: Success! Content length: {len(content)} chars")
            return content
        else:
            logger.error(f"❌ ANTHROPIC: Error {response.status_code}: {response.text}")
            raise Exception(f"Anthropic API error {response.status_code}: {response.text}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the active provider"""
        info = {
            'provider': self.active_provider,
            'has_api_key': bool(self.api_key),
            'is_initialized': bool(self.client),
            'current_model': self.current_model
        }
        
        if self.active_provider == 'groq':
            info['available_models'] = self.GROQ_MODELS
            info['recommended_model'] = self.GROQ_MODELS[0]
        
        return info
