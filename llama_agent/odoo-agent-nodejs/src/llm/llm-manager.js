import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { ChatOpenAI } from '@langchain/openai';
import { ChatAnthropic } from '@langchain/anthropic';
import config from '../config/config.js';

/**
 * LLM Manager - Provides unified interface for multiple LLM providers
 */
export class LLMManager {
  constructor(provider = null) {
    this.provider = provider || config.llm.provider;
    this.temperature = config.llm.temperature;
    this.maxTokens = config.llm.maxTokens;
    this.llm = null;
  }

  /**
   * Initialize and return the configured LLM instance
   */
  async getLLM() {
    if (this.llm) {
      return this.llm;
    }

    switch (this.provider) {
      case 'gemini':
        this.llm = this.getGeminiLLM();
        break;
      case 'openai':
        this.llm = this.getOpenAILLM();
        break;
      case 'anthropic':
        this.llm = this.getAnthropicLLM();
        break;
      default:
        throw new Error(`Unsupported LLM provider: ${this.provider}`);
    }

    return this.llm;
  }

  /**
   * Get Gemini LLM instance
   */
  getGeminiLLM() {
    if (!config.llm.gemini.apiKey) {
      throw new Error('GEMINI_API_KEY is not configured');
    }

    return new ChatGoogleGenerativeAI({
      apiKey: config.llm.gemini.apiKey,
      modelName: config.llm.gemini.model,
      temperature: this.temperature,
      maxOutputTokens: this.maxTokens
    });
  }

  /**
   * Get OpenAI LLM instance
   */
  getOpenAILLM() {
    if (!config.llm.openai.apiKey) {
      throw new Error('OPENAI_API_KEY is not configured');
    }

    return new ChatOpenAI({
      openAIApiKey: config.llm.openai.apiKey,
      modelName: config.llm.openai.model,
      temperature: this.temperature,
      maxTokens: this.maxTokens
    });
  }

  /**
   * Get Anthropic LLM instance
   */
  getAnthropicLLM() {
    if (!config.llm.anthropic.apiKey) {
      throw new Error('ANTHROPIC_API_KEY is not configured');
    }

    return new ChatAnthropic({
      anthropicApiKey: config.llm.anthropic.apiKey,
      modelName: config.llm.anthropic.model,
      temperature: this.temperature,
      maxTokens: this.maxTokens
    });
  }

  /**
   * Invoke the LLM with a prompt
   * @param {string} prompt - The prompt to send to the LLM
   * @returns {Promise<string>} The LLM response
   */
  async invoke(prompt) {
    const llm = await this.getLLM();
    const response = await llm.invoke(prompt);

    // Extract content from response
    if (typeof response === 'string') {
      return response;
    }

    if (response.content) {
      return response.content;
    }

    if (response.text) {
      return response.text;
    }

    return String(response);
  }

  /**
   * Get the current provider name
   */
  getProviderName() {
    return this.provider;
  }

  /**
   * Switch to a different provider
   */
  switchProvider(newProvider) {
    if (!['gemini', 'openai', 'anthropic'].includes(newProvider)) {
      throw new Error(`Invalid provider: ${newProvider}`);
    }
    this.provider = newProvider;
    this.llm = null; // Reset LLM instance
  }
}

export default LLMManager;
