#!/usr/bin/env python3
"""
LLM Configuration Manager for Odoo Agent
Handles different LLM providers using LangChain
"""

import os
from enum import Enum
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from langchain_core.language_models import BaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()


class LLMProvider(Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMConfig:
    """Configuration manager for different LLM providers"""
    
    def __init__(self, provider: str = None):
        self.provider = LLMProvider(provider or os.getenv("LLM_PROVIDER", "gemini"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "16384"))
        
    def get_llm(self) -> BaseLLM:
        """Get configured LLM instance based on provider"""
        
        if self.provider == LLMProvider.GEMINI:
            return self._get_gemini_llm()
        elif self.provider == LLMProvider.OPENAI:
            return self._get_openai_llm()
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._get_anthropic_llm()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _get_gemini_llm(self) -> ChatGoogleGenerativeAI:
        """Configure Gemini LLM"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def _get_openai_llm(self) -> ChatOpenAI:
        """Configure OpenAI LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def _get_anthropic_llm(self) -> ChatAnthropic:
        """Configure Anthropic LLM"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        return {
            "provider": self.provider.value,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self._get_model_name()
        }
    
    def _get_model_name(self) -> str:
        """Get the model name for current provider"""
        if self.provider == LLMProvider.GEMINI:
            return "gemini-2.0-flash-exp"
        elif self.provider == LLMProvider.OPENAI:
            return os.getenv("OPENAI_MODEL", "gpt-4")
        elif self.provider == LLMProvider.ANTHROPIC:
            return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        return "unknown"