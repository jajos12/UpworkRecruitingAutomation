"""Factory for creating AI analyzer instances."""

import os
from typing import Optional
from src.ai_providers.base_analyzer import BaseAIAnalyzer
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_ai_analyzer(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[BaseAIAnalyzer]:
    """
    Factory function to create an AI analyzer instance.
    
    Args:
        provider: AI provider name ('openai', 'claude', 'gemini')
                 If None, reads from AI_PROVIDER env var
        api_key: API key for the provider
                If None, reads from provider-specific env var
        model: Model name to use
              If None, uses provider default
              
    Returns:
        Configured AI analyzer instance or None if unavailable
        
    Example:
        # Auto-detect from environment
        analyzer = create_ai_analyzer()
        
        # Explicit provider
        analyzer = create_ai_analyzer(
            provider='openai',
            api_key='sk-...',
            model='gpt-4o-mini'
        )
    """
    
    # Debug/Get environment keys
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    
    # Auto-detect provider from environment if not specified
    if provider is None:
        env_provider = os.getenv('AI_PROVIDER')
        if env_provider:
            provider = env_provider.lower()
        else:
            # Smart detection based on available keys
            if openai_key:
                provider = 'openai'
                logger.info("Auto-detected OpenAI provider (OPENAI_API_KEY found)")
            elif anthropic_key:
                provider = 'claude'
                logger.info("Auto-detected Claude provider (ANTHROPIC_API_KEY found)")
            elif google_key:
                provider = 'gemini'
                logger.info("Auto-detected Gemini provider (GOOGLE_API_KEY found)")
            else:
                logger.warning("No AI provider specified and no API keys found in environment")
                return None
    
    logger.info(f"Using AI analyzer provider: '{provider}'")
    
    try:
        if provider == 'openai':
            from src.ai_providers.openai_analyzer import OpenAIAnalyzer
            
            if api_key is None:
                api_key = openai_key
            
            if not api_key:
                logger.warning("OpenAI API key not provided")
                return None
            
            if not model:  # Handles None and empty string
                model = os.getenv('AI_MODEL', 'gpt-4o-mini')
            
            return OpenAIAnalyzer(api_key=api_key, model=model)
        
        elif provider == 'claude':
            from src.ai_providers.claude_analyzer import ClaudeAnalyzer
            
            if api_key is None:
                api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not api_key:
                logger.warning("Anthropic API key not provided")
                return None
            
            if model is None:
                model = os.getenv('AI_MODEL', 'claude-sonnet-4-20250514')
            
            return ClaudeAnalyzer(api_key=api_key, model=model)
        
        elif provider == 'gemini':
            from src.ai_providers.gemini_analyzer import GeminiAnalyzer
            
            if api_key is None:
                api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                logger.warning("Google API key not provided")
                return None
            
            if model is None:
                model = os.getenv('AI_MODEL', 'gemini-pro')
            
            return GeminiAnalyzer(api_key=api_key, model=model)
        
        else:
            logger.error(f"Unknown AI provider: {provider}")
            logger.info("Supported providers: openai, claude, gemini")
            return None
            
    except ImportError as e:
        logger.error(f"Failed to import {provider} analyzer: {e}")
        logger.info(f"Make sure to install the required package for {provider}")
        return None
    except Exception as e:
        logger.error(f"Failed to create AI analyzer: {e}")
        return None


def get_available_providers() -> list:
    """
    Get list of available AI providers based on environment variables.
    
    Returns:
        List of provider names that have API keys configured
    """
    available = []
    
    if os.getenv('OPENAI_API_KEY'):
        available.append('openai')
    if os.getenv('ANTHROPIC_API_KEY'):
        available.append('claude')
    if os.getenv('GOOGLE_API_KEY'):
        available.append('gemini')
    
    return available
