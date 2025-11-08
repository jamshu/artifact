import { decode } from '@toon-format/toon';

/**
 * Toon Parser - Parse Toon format responses with JSON fallback
 */
export class ToonParser {
  /**
   * Parse a response that may be in Toon or JSON format
   * @param {string} responseText - The raw response text
   * @returns {object} Parsed data structure
   */
  static parse(responseText) {
    if (!responseText || typeof responseText !== 'string') {
      throw new Error('Invalid response: expected string');
    }

    // Try Toon format first
    try {
      const toonData = this.parseToon(responseText);
      if (toonData) {
        return toonData;
      }
    } catch (toonError) {
      console.log('Toon parsing failed, trying JSON fallback:', toonError.message);
    }

    // Fallback to JSON
    try {
      const jsonData = this.parseJSON(responseText);
      return jsonData;
    } catch (jsonError) {
      throw new Error(`Failed to parse response as Toon or JSON:\nToon error: ${toonError?.message}\nJSON error: ${jsonError.message}`);
    }
  }

  /**
   * Parse Toon format specifically
   * @param {string} text - Toon formatted text
   * @returns {object} Parsed object
   */
  static parseToon(text) {
    // Clean up markdown code blocks if present
    let cleaned = text.trim();

    if (cleaned.includes('```toon')) {
      const start = cleaned.indexOf('```toon') + 7;
      const end = cleaned.lastIndexOf('```');
      if (end > start) {
        cleaned = cleaned.slice(start, end).trim();
      }
    } else if (cleaned.startsWith('```')) {
      cleaned = cleaned.replace(/^```[\w]*\n/, '').replace(/\n```$/, '');
    }

    // Use the official Toon parser (decode)
    const parsed = decode(cleaned);

    // Validate parsed result
    if (!parsed || typeof parsed !== 'object') {
      throw new Error('Toon parser returned invalid result');
    }

    return parsed;
  }

  /**
   * Parse JSON with various cleanup strategies
   * @param {string} text - JSON text (possibly wrapped in markdown)
   * @returns {object} Parsed object
   */
  static parseJSON(text) {
    let cleaned = text.trim();

    // Remove markdown code blocks
    if (cleaned.startsWith('```json')) {
      cleaned = cleaned.slice(7);
      if (cleaned.endsWith('```')) {
        cleaned = cleaned.slice(0, -3);
      }
    } else if (cleaned.startsWith('```')) {
      cleaned = cleaned.replace(/^```[\w]*\n/, '').replace(/\n```$/, '');
    }

    cleaned = cleaned.trim();

    // Try direct parse first
    try {
      return JSON.parse(cleaned);
    } catch (e) {
      // Try to extract JSON from text
      return this.extractJSON(cleaned);
    }
  }

  /**
   * Extract JSON object from text that may contain other content
   * @param {string} text - Text containing JSON
   * @returns {object} Extracted and parsed JSON
   */
  static extractJSON(text) {
    // Find the first { or [
    const startBrace = text.indexOf('{');
    const startBracket = text.indexOf('[');

    let start = -1;
    let startChar = null;

    if (startBrace !== -1 && (startBracket === -1 || startBrace < startBracket)) {
      start = startBrace;
      startChar = '{';
    } else if (startBracket !== -1) {
      start = startBracket;
      startChar = '[';
    }

    if (start === -1) {
      throw new Error('No JSON object or array found in text');
    }

    // Find matching closing brace/bracket
    let count = 0;
    let end = start;
    const closeChar = startChar === '{' ? '}' : ']';

    for (let i = start; i < text.length; i++) {
      if (text[i] === startChar) count++;
      if (text[i] === closeChar) count--;

      if (count === 0) {
        end = i + 1;
        break;
      }
    }

    if (count !== 0) {
      throw new Error('Unbalanced braces/brackets in JSON');
    }

    const jsonStr = text.slice(start, end);
    return JSON.parse(jsonStr);
  }

  /**
   * Parse module creation response (Toon or JSON)
   * Expected Toon format:
   * module_info{name,description,version,category}:
   *  module_name,description,16.0.1.0.0,Custom
   *
   * files[N]{path,content,description}:
   *  path1,content1,desc1
   *  path2,content2,desc2
   */
  static parseModuleCreation(responseText) {
    const data = this.parse(responseText);

    // Normalize to consistent structure
    const result = {
      module_info: null,
      files: []
    };

    // Handle both Toon and JSON structures
    if (data.module_info) {
      if (Array.isArray(data.module_info) && data.module_info.length > 0) {
        // Toon format - array with single object
        result.module_info = data.module_info[0];
      } else if (typeof data.module_info === 'object') {
        // JSON format - direct object
        result.module_info = data.module_info;
      }
    }

    if (data.files) {
      result.files = Array.isArray(data.files) ? data.files : [];
    }

    return result;
  }

  /**
   * Parse module customization response
   */
  static parseModuleCustomization(responseText) {
    const data = this.parse(responseText);

    const result = {
      analysis: null,
      files: []
    };

    if (data.analysis) {
      result.analysis = Array.isArray(data.analysis) ? data.analysis[0] : data.analysis;
    }

    if (data.files) {
      result.files = Array.isArray(data.files) ? data.files : [];
    }

    return result;
  }

  /**
   * Parse debug issue response
   */
  static parseDebugIssue(responseText) {
    const data = this.parse(responseText);

    const result = {
      diagnosis: null,
      solution: null,
      fixes: [],
      testing_steps: [],
      prevention_tips: []
    };

    if (data.diagnosis) {
      result.diagnosis = Array.isArray(data.diagnosis) ? data.diagnosis[0] : data.diagnosis;
    }

    if (data.solution) {
      result.solution = Array.isArray(data.solution) ? data.solution[0] : data.solution;
    }

    if (data.fixes) {
      result.fixes = Array.isArray(data.fixes) ? data.fixes : [];
    }

    if (data.testing_steps) {
      result.testing_steps = Array.isArray(data.testing_steps) ? data.testing_steps : [];
    }

    if (data.prevention_tips) {
      result.prevention_tips = Array.isArray(data.prevention_tips) ? data.prevention_tips : [];
    }

    return result;
  }

  /**
   * Parse code analysis response
   */
  static parseCodeAnalysis(responseText) {
    const data = this.parse(responseText);

    const result = {
      summary: null,
      issues: [],
      best_practices: [],
      security_concerns: []
    };

    if (data.summary) {
      result.summary = Array.isArray(data.summary) ? data.summary[0] : data.summary;
    }

    if (data.issues) {
      result.issues = Array.isArray(data.issues) ? data.issues : [];
    }

    if (data.best_practices) {
      result.best_practices = Array.isArray(data.best_practices) ? data.best_practices : [];
    }

    if (data.security_concerns) {
      result.security_concerns = Array.isArray(data.security_concerns) ? data.security_concerns : [];
    }

    return result;
  }
}

export default ToonParser;
