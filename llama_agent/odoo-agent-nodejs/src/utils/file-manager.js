import fs from 'fs-extra';
import path from 'path';
import config from '../config/config.js';

/**
 * File Manager - Handle file operations with backup support
 */
export class FileManager {
  /**
   * Create a backup of a file before modification
   * @param {string} filePath - Path to file
   * @returns {Promise<string|null>} Backup file path or null if file doesn't exist
   */
  static async createBackup(filePath) {
    if (!config.agent.backupFiles) {
      return null;
    }

    try {
      if (await fs.pathExists(filePath)) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = `${filePath}.backup_${timestamp}`;

        await fs.copy(filePath, backupPath);
        console.log(`✓ Backup created: ${backupPath}`);
        return backupPath;
      }
    } catch (error) {
      console.error(`Warning: Failed to create backup for ${filePath}:`, error.message);
    }

    return null;
  }

  /**
   * Create a new file
   * @param {string} filePath - Path to file
   * @param {string} content - File content
   * @returns {Promise<boolean>} Success status
   */
  static async createFile(filePath, content) {
    try {
      // Ensure directory exists
      const dir = path.dirname(filePath);
      await fs.ensureDir(dir);

      // Write file
      await fs.writeFile(filePath, content, 'utf-8');
      console.log(`✓ Created: ${filePath}`);
      return true;
    } catch (error) {
      console.error(`✗ Failed to create ${filePath}:`, error.message);
      return false;
    }
  }

  /**
   * Modify an existing file
   * @param {string} filePath - Path to file
   * @param {string} content - New content
   * @returns {Promise<boolean>} Success status
   */
  static async modifyFile(filePath, content) {
    try {
      // Create backup first
      await this.createBackup(filePath);

      // Write new content
      await fs.writeFile(filePath, content, 'utf-8');
      console.log(`✓ Modified: ${filePath}`);
      return true;
    } catch (error) {
      console.error(`✗ Failed to modify ${filePath}:`, error.message);
      return false;
    }
  }

  /**
   * Delete a file
   * @param {string} filePath - Path to file
   * @returns {Promise<boolean>} Success status
   */
  static async deleteFile(filePath) {
    try {
      // Create backup first
      await this.createBackup(filePath);

      // Delete file
      await fs.remove(filePath);
      console.log(`✓ Deleted: ${filePath}`);
      return true;
    } catch (error) {
      console.error(`✗ Failed to delete ${filePath}:`, error.message);
      return false;
    }
  }

  /**
   * Read file content
   * @param {string} filePath - Path to file
   * @returns {Promise<string|null>} File content or null
   */
  static async readFile(filePath) {
    try {
      if (await fs.pathExists(filePath)) {
        return await fs.readFile(filePath, 'utf-8');
      }
    } catch (error) {
      console.error(`Failed to read ${filePath}:`, error.message);
    }
    return null;
  }

  /**
   * Check if file exists
   * @param {string} filePath - Path to file
   * @returns {Promise<boolean>}
   */
  static async exists(filePath) {
    return await fs.pathExists(filePath);
  }

  /**
   * Get all files in a directory recursively
   * @param {string} dirPath - Directory path
   * @param {Array<string>} extensions - File extensions to include (e.g., ['.py', '.xml'])
   * @returns {Promise<Array<string>>} Array of file paths
   */
  static async getFilesRecursively(dirPath, extensions = null) {
    const files = [];

    try {
      const items = await fs.readdir(dirPath);

      for (const item of items) {
        const fullPath = path.join(dirPath, item);
        const stat = await fs.stat(fullPath);

        if (stat.isDirectory()) {
          // Skip common directories to ignore
          if (!['__pycache__', '.git', 'node_modules', '.pytest_cache'].includes(item)) {
            const subFiles = await this.getFilesRecursively(fullPath, extensions);
            files.push(...subFiles);
          }
        } else if (stat.isFile()) {
          if (!extensions || extensions.some(ext => fullPath.endsWith(ext))) {
            files.push(fullPath);
          }
        }
      }
    } catch (error) {
      console.error(`Error reading directory ${dirPath}:`, error.message);
    }

    return files;
  }

  /**
   * Get module structure (files and directories)
   * @param {string} modulePath - Path to module
   * @returns {Promise<object>} Module structure
   */
  static async getModuleStructure(modulePath) {
    const structure = {
      path: modulePath,
      exists: await fs.pathExists(modulePath),
      files: [],
      directories: []
    };

    if (!structure.exists) {
      return structure;
    }

    try {
      const items = await fs.readdir(modulePath);

      for (const item of items) {
        const fullPath = path.join(modulePath, item);
        const stat = await fs.stat(fullPath);

        if (stat.isDirectory() && !item.startsWith('.') && !item.startsWith('__pycache__')) {
          structure.directories.push(item);
        } else if (stat.isFile() && !item.startsWith('.')) {
          structure.files.push(item);
        }
      }
    } catch (error) {
      console.error(`Error analyzing module structure:`, error.message);
    }

    return structure;
  }

  /**
   * Apply a FileChange
   * @param {FileChange} change - FileChange to apply
   * @returns {Promise<boolean>} Success status
   */
  static async applyFileChange(change) {
    if (!change.approved) {
      console.log(`⊘ Skipped (not approved): ${change.filePath}`);
      return false;
    }

    switch (change.action) {
      case 'create':
        return await this.createFile(change.filePath, change.newContent);
      case 'modify':
        return await this.modifyFile(change.filePath, change.newContent);
      case 'delete':
        return await this.deleteFile(change.filePath);
      default:
        console.error(`Unknown action: ${change.action}`);
        return false;
    }
  }

  /**
   * Apply multiple FileChanges
   * @param {Array<FileChange>} changes - Array of FileChanges
   * @returns {Promise<object>} Results summary
   */
  static async applyFileChanges(changes) {
    const results = {
      total: changes.length,
      successful: 0,
      failed: 0,
      skipped: 0
    };

    for (const change of changes) {
      if (!change.approved) {
        results.skipped++;
        continue;
      }

      const success = await this.applyFileChange(change);
      if (success) {
        results.successful++;
      } else {
        results.failed++;
      }
    }

    return results;
  }
}

export default FileManager;
