import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Application configuration
 */
const config = {
  // LLM Configuration
  llm: {
    provider: process.env.LLM_PROVIDER || 'gemini',
    temperature: parseFloat(process.env.LLM_TEMPERATURE || '0.1'),
    maxTokens: parseInt(process.env.LLM_MAX_TOKENS || '16384'),

    // Gemini settings
    gemini: {
      apiKey: process.env.GEMINI_API_KEY,
      model: process.env.GEMINI_MODEL || 'gemini-1.5-pro'
    },

    // OpenAI settings
    openai: {
      apiKey: process.env.OPENAI_API_KEY,
      model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview'
    },

    // Anthropic settings
    anthropic: {
      apiKey: process.env.ANTHROPIC_API_KEY,
      model: process.env.ANTHROPIC_MODEL || 'claude-3-5-sonnet-20241022'
    }
  },

  // Odoo Configuration
  odoo: {
    addonsPath: process.env.ODOO_ADDONS_PATH || './addons',
    version: process.env.ODOO_VERSION || '16.0'
  },

  // Agent Settings
  agent: {
    autoApprove: process.env.AUTO_APPROVE_CHANGES === 'true',
    backupFiles: process.env.BACKUP_FILES !== 'false',
    useToonFormat: process.env.USE_TOON_FORMAT !== 'false'
  }
};

/**
 * Validate required configuration
 */
export function validateConfig() {
  const errors = [];

  const provider = config.llm.provider;

  if (provider === 'gemini' && !config.llm.gemini.apiKey) {
    errors.push('GEMINI_API_KEY is required when using Gemini provider');
  }

  if (provider === 'openai' && !config.llm.openai.apiKey) {
    errors.push('OPENAI_API_KEY is required when using OpenAI provider');
  }

  if (provider === 'anthropic' && !config.llm.anthropic.apiKey) {
    errors.push('ANTHROPIC_API_KEY is required when using Anthropic provider');
  }

  if (!['gemini', 'openai', 'anthropic'].includes(provider)) {
    errors.push(`Invalid LLM_PROVIDER: ${provider}. Must be one of: gemini, openai, anthropic`);
  }

  if (errors.length > 0) {
    throw new Error(`Configuration errors:\n${errors.join('\n')}`);
  }

  return true;
}

export default config;
