"""
AI Provider Manager for Gem AI - BULLETPROOF VERSION
Works with direct API calls - NO SDK ISSUES
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
    
    def __init__(self):
        self.active_provider = None
        self.api_key = None
        self.client = "direct_api"  # We'll use direct API calls
        self._detect_provider()
    
    def _detect_provider(self):
        """Detect which AI provider to use based on available API keys"""
        for env_var, provider_name in self.PROVIDERS.items():
            api_key = os.getenv(env_var)
            if api_key:
                self.active_provider = provider_name
                self.api_key = api_key
                logger.info(f"✅ Detected AI provider: {provider_name}")
                logger.info(f"✅ API Key (first 10 chars): {api_key[:10]}...")
                logger.info(f"✅ API Key (last 4 chars): ...{api_key[-4:]}")
                return
        
        logger.error("❌ No AI provider API key found!")
        raise ValueError("No AI API key found")
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        """Generate completion using direct API calls"""
        
        logger.info("="*80)
        logger.info(f"🤖 STARTING AI COMPLETION")
        logger.info(f"🤖 Provider: {self.active_provider}")
        logger.info(f"📝 Prompt length: {len(prompt)} chars")
        logger.info(f"🎛️ Settings: temp={temperature}, max_tokens={max_tokens}")
        
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
        """Direct Groq API call - 100% bulletproof"""
        
        logger.info("🚀 GROQ: Preparing direct API call")
        
        # Get model from environment or use default
        model = os.getenv('GROQ_MODEL', 'mixtral-8x7b-32768')
        
        # Prepare the request
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
        logger.info(f"📡 GROQ: Headers: Authorization=Bearer {self.api_key[:10]}..., Content-Type=application/json")
        
        try:
            logger.info("📡 GROQ: Making HTTP POST request...")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            logger.info(f"📡 GROQ: Response Status Code: {response.status_code}")
            logger.info(f"📡 GROQ: Response Headers: {dict(response.headers)}")
            
            # Log the full response for debugging
            try:
                response_text = response.text
                logger.info(f"📡 GROQ: Response Body (first 500 chars): {response_text[:500]}")
            except:
                logger.warning("⚠️ GROQ: Could not read response body")
            
            if response.status_code == 200:
                logger.info("✅ GROQ: Request successful!")
                
                try:
                    result_data = response.json()
                    logger.info(f"✅ GROQ: JSON parsed successfully")
                    logger.info(f"✅ GROQ: Response keys: {result_data.keys()}")
                    
                    if 'choices' in result_data and len(result_data['choices']) > 0:
                        content = result_data['choices'][0]['message']['content']
                        logger.info(f"✅ GROQ: Extracted content ({len(content)} chars)")
                        logger.info(f"📄 GROQ: Content preview: {content[:200]}...")
                        return content
                    else:
                        logger.error(f"❌ GROQ: Unexpected response structure: {result_data}")
                        raise Exception("Invalid response structure from Groq API")
                        
                except json.JSONDecodeError as je:
                    logger.error(f"❌ GROQ: JSON decode error: {je}")
                    logger.error(f"❌ GROQ: Raw response: {response.text}")
                    raise Exception(f"Failed to parse Groq response: {je}")
                    
            else:
                # Non-200 status code
                error_text = response.text
                logger.error(f"❌ GROQ: API returned error status {response.status_code}")
                logger.error(f"❌ GROQ: Error response: {error_text}")
                
                # Try to parse error details
                try:
                    error_json = response.json()
                    logger.error(f"❌ GROQ: Error details: {error_json}")
                except:
                    pass
                
                raise Exception(f"Groq API error {response.status_code}: {error_text}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ GROQ: Request timed out after 120 seconds")
            raise Exception("Groq API request timed out")
            
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"❌ GROQ: Connection error: {ce}")
            raise Exception(f"Failed to connect to Groq API: {ce}")
            
        except requests.exceptions.RequestException as re:
            logger.error(f"❌ GROQ: Request exception: {re}")
            raise Exception(f"Groq API request failed: {re}")
    
    def _openai_api(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Direct OpenAI API call"""
        model = os.getenv('OPENAI_MODEL', 'gpt-4')
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
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenAI API error {response.status_code}: {response.text}")
    
    def _anthropic_api(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Direct Anthropic API call"""
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
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            raise Exception(f"Anthropic API error {response.status_code}: {response.text}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the active provider"""
        return {
            'provider': self.active_provider,
            'has_api_key': bool(self.api_key),
            'is_initialized': bool(self.client)
        }
