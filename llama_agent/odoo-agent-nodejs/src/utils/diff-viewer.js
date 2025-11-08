import * as diff from 'diff';
import chalk from 'chalk';

/**
 * Diff Viewer - Display file differences with colors
 */
export class DiffViewer {
  /**
   * Show a colored diff between original and new content
   * @param {string} original - Original content
   * @param {string} modified - Modified content
   * @param {string} filename - Filename for context
   */
  static showDiff(original, modified, filename = 'file') {
    const differences = diff.createPatch(filename, original, modified, '', '');
    const lines = differences.split('\n');

    console.log(chalk.bold(`\n${'='.repeat(80)}`));
    console.log(chalk.bold.cyan(`Diff for: ${filename}`));
    console.log(chalk.bold(`${'='.repeat(80)}\n`));

    for (const line of lines) {
      if (line.startsWith('+++') || line.startsWith('---')) {
        console.log(chalk.bold.white(line));
      } else if (line.startsWith('+')) {
        console.log(chalk.green(line));
      } else if (line.startsWith('-')) {
        console.log(chalk.red(line));
      } else if (line.startsWith('@@')) {
        console.log(chalk.cyan(line));
      } else {
        console.log(chalk.gray(line));
      }
    }

    console.log(chalk.bold(`${'='.repeat(80)}\n`));
  }

  /**
   * Show unified diff for file creation
   * @param {string} content - New file content
   * @param {string} filename - Filename
   */
  static showNewFile(content, filename) {
    console.log(chalk.bold(`\n${'='.repeat(80)}`));
    console.log(chalk.bold.green(`New File: ${filename}`));
    console.log(chalk.bold(`${'='.repeat(80)}\n`));

    const lines = content.split('\n');
    const maxLines = 50; // Show first 50 lines for new files

    lines.slice(0, maxLines).forEach((line, idx) => {
      console.log(chalk.green(`${String(idx + 1).padStart(4)} + ${line}`));
    });

    if (lines.length > maxLines) {
      console.log(chalk.yellow(`\n... (${lines.length - maxLines} more lines) ...\n`));
    }

    console.log(chalk.bold(`${'='.repeat(80)}\n`));
  }

  /**
   * Show file deletion
   * @param {string} content - Original file content
   * @param {string} filename - Filename
   */
  static showDeletedFile(content, filename) {
    console.log(chalk.bold(`\n${'='.repeat(80)}`));
    console.log(chalk.bold.red(`Deleted File: ${filename}`));
    console.log(chalk.bold(`${'='.repeat(80)}\n`));

    const lines = content.split('\n');
    const maxLines = 20; // Show first 20 lines for deleted files

    lines.slice(0, maxLines).forEach((line, idx) => {
      console.log(chalk.red(`${String(idx + 1).padStart(4)} - ${line}`));
    });

    if (lines.length > maxLines) {
      console.log(chalk.yellow(`\n... (${lines.length - maxLines} more lines) ...\n`));
    }

    console.log(chalk.bold(`${'='.repeat(80)}\n`));
  }

  /**
   * Show diff statistics
   * @param {string} original - Original content
   * @param {string} modified - Modified content
   * @returns {object} Statistics
   */
  static getDiffStats(original, modified) {
    const changes = diff.diffLines(original, modified);

    const stats = {
      additions: 0,
      deletions: 0,
      changes: 0
    };

    for (const part of changes) {
      if (part.added) {
        stats.additions += part.count || 0;
      } else if (part.removed) {
        stats.deletions += part.count || 0;
      }
    }

    stats.changes = stats.additions + stats.deletions;

    return stats;
  }

  /**
   * Show diff summary
   * @param {string} original - Original content
   * @param {string} modified - Modified content
   */
  static showDiffSummary(original, modified) {
    const stats = this.getDiffStats(original, modified);

    console.log(chalk.green(`  +${stats.additions} lines added`));
    console.log(chalk.red(`  -${stats.deletions} lines removed`));
    console.log(chalk.cyan(`  ~${stats.changes} total changes`));
  }

  /**
   * Show a FileChange diff
   * @param {FileChange} change - FileChange object
   */
  static showFileChange(change) {
    const filename = change.getFileName();

    if (change.isCreate()) {
      this.showNewFile(change.newContent, filename);
    } else if (change.isDelete()) {
      this.showDeletedFile(change.originalContent, filename);
    } else if (change.isModify()) {
      this.showDiff(change.originalContent, change.newContent, filename);
    }

    // Show description
    if (change.description) {
      console.log(chalk.blue.bold('Description: ') + chalk.white(change.description));
      console.log();
    }
  }

  /**
   * Show compact diff (first few lines only)
   * @param {FileChange} change - FileChange object
   * @param {number} maxLines - Maximum lines to show
   */
  static showCompactDiff(change, maxLines = 10) {
    const filename = change.getFileName();

    console.log(chalk.bold(`\n${change.action.toUpperCase()}: ${filename}`));

    if (change.description) {
      console.log(chalk.gray(`  ${change.description}`));
    }

    if (change.isCreate()) {
      const lines = change.newContent.split('\n').slice(0, maxLines);
      lines.forEach(line => console.log(chalk.green(`  + ${line.slice(0, 70)}...`)));
      if (change.newContent.split('\n').length > maxLines) {
        console.log(chalk.yellow(`  ... (${change.newContent.split('\n').length - maxLines} more lines)`));
      }
    } else if (change.isModify()) {
      const stats = this.getDiffStats(change.originalContent, change.newContent);
      console.log(chalk.green(`  +${stats.additions}`) + chalk.red(` -${stats.deletions}`) + chalk.gray(` lines`));
    } else if (change.isDelete()) {
      console.log(chalk.red(`  File will be deleted`));
    }

    console.log();
  }
}

export default DiffViewer;
