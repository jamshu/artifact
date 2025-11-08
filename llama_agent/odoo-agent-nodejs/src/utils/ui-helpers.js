import chalk from 'chalk';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import { DiffViewer } from './diff-viewer.js';

/**
 * UI Helpers - Terminal UI utilities
 */
export class UIHelpers {
  /**
   * Show a welcome banner
   */
  static showBanner() {
    console.log(chalk.bold.cyan(`
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              Odoo Agent - Node.js Edition                     ║
║         AI-Powered Odoo Development Assistant                 ║
║            Using Toon Format for Token Efficiency             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    `));
  }

  /**
   * Show changes summary table
   * @param {Array<FileChange>} changes - Array of FileChange objects
   */
  static showChangesSummary(changes) {
    const table = new Table({
      head: [
        chalk.bold('Action'),
        chalk.bold('File'),
        chalk.bold('Description')
      ],
      colWidths: [12, 35, 50],
      wordWrap: true
    });

    for (const change of changes) {
      const action = change.action.toUpperCase();
      const actionColored = change.isCreate() ? chalk.green(action)
        : change.isModify() ? chalk.yellow(action)
        : chalk.red(action);

      table.push([
        actionColored,
        change.getFileName(),
        change.description.slice(0, 47) + (change.description.length > 47 ? '...' : '')
      ]);
    }

    console.log(chalk.bold('\n📋 Changes Summary:\n'));
    console.log(table.toString());
    console.log();
  }

  /**
   * Ask user for approval of changes
   * @param {Array<FileChange>} changes - Array of FileChange objects
   * @returns {Promise<boolean>} True if approved, false otherwise
   */
  static async askForApproval(changes) {
    this.showChangesSummary(changes);

    const { reviewDetails } = await inquirer.prompt([{
      type: 'confirm',
      name: 'reviewDetails',
      message: 'Would you like to review the changes in detail?',
      default: true
    }]);

    if (reviewDetails) {
      for (let i = 0; i < changes.length; i++) {
        const change = changes[i];

        console.log(chalk.bold.cyan(`\n[${ i + 1}/${changes.length}] Reviewing: ${change.filePath}\n`));

        DiffViewer.showFileChange(change);

        const { action } = await inquirer.prompt([{
          type: 'list',
          name: 'action',
          message: `What would you like to do with this file?`,
          choices: [
            { name: '✓ Approve this change', value: 'approve' },
            { name: '⊘ Skip this change', value: 'skip' },
            { name: '✗ Cancel all changes', value: 'cancel' }
          ],
          default: 'approve'
        }]);

        if (action === 'cancel') {
          console.log(chalk.red('\n✗ Operation cancelled by user\n'));
          return false;
        }

        if (action === 'approve') {
          change.approve();
        } else {
          change.reject();
        }
      }
    } else {
      // Quick review - show compact diffs
      console.log(chalk.bold('\n📄 Quick Review:\n'));
      for (const change of changes) {
        DiffViewer.showCompactDiff(change, 5);
      }
    }

    // Final confirmation
    const approvedCount = changes.filter(c => c.approved || !reviewDetails).length;

    if (approvedCount === 0) {
      console.log(chalk.yellow('\n⚠ No changes were approved\n'));
      return false;
    }

    // If we didn't do detailed review, approve all by default
    if (!reviewDetails) {
      changes.forEach(c => c.approve());
    }

    const { finalConfirm } = await inquirer.prompt([{
      type: 'confirm',
      name: 'finalConfirm',
      message: `Apply ${approvedCount} change(s)?`,
      default: true
    }]);

    if (!finalConfirm) {
      console.log(chalk.red('\n✗ Operation cancelled by user\n'));
      return false;
    }

    return true;
  }

  /**
   * Show a loading spinner (simple animation)
   * @param {string} message - Loading message
   * @returns {object} Spinner object with stop() method
   */
  static showSpinner(message) {
    const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    let i = 0;

    const interval = setInterval(() => {
      process.stdout.write(`\r${chalk.cyan(frames[i])} ${message}`);
      i = (i + 1) % frames.length;
    }, 80);

    return {
      stop: (finalMessage = null) => {
        clearInterval(interval);
        process.stdout.write('\r' + ' '.repeat(100) + '\r');
        if (finalMessage) {
          console.log(finalMessage);
        }
      }
    };
  }

  /**
   * Show a success message
   * @param {string} message - Success message
   */
  static showSuccess(message) {
    console.log(chalk.green(`\n✓ ${message}\n`));
  }

  /**
   * Show an error message
   * @param {string} message - Error message
   */
  static showError(message) {
    console.log(chalk.red(`\n✗ ${message}\n`));
  }

  /**
   * Show a warning message
   * @param {string} message - Warning message
   */
  static showWarning(message) {
    console.log(chalk.yellow(`\n⚠ ${message}\n`));
  }

  /**
   * Show an info message
   * @param {string} message - Info message
   */
  static showInfo(message) {
    console.log(chalk.blue(`\nℹ ${message}\n`));
  }

  /**
   * Show application results
   * @param {object} results - Results object with successful, failed, skipped counts
   */
  static showResults(results) {
    console.log(chalk.bold('\n📊 Results:\n'));

    const table = new Table({
      head: ['Status', 'Count'],
      colWidths: [20, 10]
    });

    table.push(
      [chalk.green('Successful'), chalk.green(results.successful)],
      [chalk.red('Failed'), chalk.red(results.failed)],
      [chalk.yellow('Skipped'), chalk.yellow(results.skipped)],
      [chalk.bold('Total'), chalk.bold(results.total)]
    );

    console.log(table.toString());
    console.log();

    if (results.successful > 0) {
      this.showSuccess('Operation completed successfully!');
    }

    if (results.failed > 0) {
      this.showError(`${results.failed} operation(s) failed`);
    }
  }

  /**
   * Show debug information
   * @param {object} debugInfo - Debug information
   */
  static showDebugInfo(debugInfo) {
    console.log(chalk.bold.cyan('\n🔍 Diagnosis:\n'));

    if (debugInfo.diagnosis) {
      console.log(chalk.yellow('Error Type: ') + debugInfo.diagnosis.error_type);
      console.log(chalk.yellow('Root Cause: ') + debugInfo.diagnosis.root_cause);
      console.log(chalk.yellow('Severity: ') + debugInfo.diagnosis.severity);
      console.log();
    }

    if (debugInfo.solution) {
      console.log(chalk.bold.green('💡 Solution:\n'));
      console.log(chalk.white(debugInfo.solution.approach));
      console.log();
      console.log(chalk.gray(debugInfo.solution.explanation));
      console.log();
    }

    if (debugInfo.testing_steps && debugInfo.testing_steps.length > 0) {
      console.log(chalk.bold.blue('🧪 Testing Steps:\n'));
      debugInfo.testing_steps.forEach((step, idx) => {
        console.log(chalk.cyan(`${idx + 1}. ${step.step}`));
        if (step.command) {
          console.log(chalk.gray(`   Command: ${step.command}`));
        }
        if (step.expected_result) {
          console.log(chalk.gray(`   Expected: ${step.expected_result}`));
        }
        console.log();
      });
    }

    if (debugInfo.prevention_tips && debugInfo.prevention_tips.length > 0) {
      console.log(chalk.bold.magenta('💡 Prevention Tips:\n'));
      debugInfo.prevention_tips.forEach((item, idx) => {
        console.log(chalk.white(`  ${idx + 1}. ${item.tip || item}`));
      });
      console.log();
    }
  }

  /**
   * Ask user to choose from a list
   * @param {string} message - Prompt message
   * @param {Array} choices - Array of choices
   * @returns {Promise<string>} Selected choice
   */
  static async askChoice(message, choices) {
    const { choice } = await inquirer.prompt([{
      type: 'list',
      name: 'choice',
      message,
      choices
    }]);

    return choice;
  }

  /**
   * Ask user for text input
   * @param {string} message - Prompt message
   * @param {string} defaultValue - Default value
   * @returns {Promise<string>} User input
   */
  static async askInput(message, defaultValue = '') {
    const { input } = await inquirer.prompt([{
      type: 'input',
      name: 'input',
      message,
      default: defaultValue
    }]);

    return input;
  }

  /**
   * Ask yes/no question
   * @param {string} message - Question
   * @param {boolean} defaultValue - Default answer
   * @returns {Promise<boolean>} Answer
   */
  static async askConfirm(message, defaultValue = true) {
    const { confirm } = await inquirer.prompt([{
      type: 'confirm',
      name: 'confirm',
      message,
      default: defaultValue
    }]);

    return confirm;
  }
}

export default UIHelpers;
