/**
 * FileChange - Represents a file operation (create, modify, delete)
 */
export class FileChange {
  /**
   * @param {string} filePath - Path to the file
   * @param {string} action - Action to perform: 'create', 'modify', 'delete'
   * @param {string} originalContent - Original content (empty for create)
   * @param {string} newContent - New content (empty for delete)
   * @param {string} description - Description of the change
   */
  constructor(filePath, action, originalContent, newContent, description) {
    this.filePath = filePath;
    this.action = action;
    this.originalContent = originalContent || '';
    this.newContent = newContent || '';
    this.description = description || '';
    this.approved = false;
  }

  /**
   * Mark this change as approved
   */
  approve() {
    this.approved = true;
  }

  /**
   * Mark this change as not approved
   */
  reject() {
    this.approved = false;
  }

  /**
   * Check if this is a create action
   */
  isCreate() {
    return this.action === 'create';
  }

  /**
   * Check if this is a modify action
   */
  isModify() {
    return this.action === 'modify';
  }

  /**
   * Check if this is a delete action
   */
  isDelete() {
    return this.action === 'delete';
  }

  /**
   * Get file name from path
   */
  getFileName() {
    return this.filePath.split('/').pop();
  }

  /**
   * Get directory path
   */
  getDirectory() {
    const parts = this.filePath.split('/');
    parts.pop();
    return parts.join('/');
  }

  /**
   * Create FileChange from parsed file data
   * @param {object} fileData - Parsed file data with path, content, action, description
   * @param {string} basePath - Base path to prepend
   * @param {string} originalContent - Original content if modifying
   * @returns {FileChange}
   */
  static fromParsedData(fileData, basePath = '', originalContent = '') {
    const fullPath = basePath ? `${basePath}/${fileData.path}` : fileData.path;
    const action = fileData.action || 'create';

    return new FileChange(
      fullPath,
      action,
      originalContent,
      fileData.content || '',
      fileData.description || ''
    );
  }

  /**
   * Create multiple FileChanges from array of parsed data
   * @param {Array} filesData - Array of parsed file data
   * @param {string} basePath - Base path to prepend
   * @returns {Array<FileChange>}
   */
  static fromParsedArray(filesData, basePath = '') {
    if (!Array.isArray(filesData)) {
      return [];
    }

    return filesData.map(fileData => {
      return FileChange.fromParsedData(fileData, basePath);
    });
  }

  /**
   * Convert to string representation
   */
  toString() {
    return `FileChange(${this.action}: ${this.filePath})`;
  }

  /**
   * Convert to JSON
   */
  toJSON() {
    return {
      filePath: this.filePath,
      action: this.action,
      originalContent: this.originalContent,
      newContent: this.newContent,
      description: this.description,
      approved: this.approved
    };
  }
}

export default FileChange;
