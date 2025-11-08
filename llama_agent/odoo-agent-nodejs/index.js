#!/usr/bin/env node

import { validateConfig } from './src/config/config.js';
import { CommandCLI } from './src/cli/commands.js';
import { InteractiveCLI } from './src/cli/interactive.js';
import chalk from 'chalk';

/**
 * Main entry point for Odoo Agent CLI
 */
async function main() {
  try {
    // Validate configuration
    validateConfig();

    // If no arguments provided, start interactive mode
    if (process.argv.length === 2) {
      const interactive = new InteractiveCLI();
      await interactive.start();
    } else {
      // Use command-based mode
      const commandCLI = new CommandCLI();
      await commandCLI.run();
    }
  } catch (error) {
    console.error(chalk.red(`\n✗ Error: ${error.message}\n`));

    if (error.message.includes('API_KEY')) {
      console.log(chalk.yellow('Make sure to configure your API keys in .env file'));
      console.log(chalk.gray('Copy .env.example to .env and fill in your API keys\n'));
    }

    process.exit(1);
  }
}

// Run the CLI
main();
