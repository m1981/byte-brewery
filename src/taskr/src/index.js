#!/usr/bin/env node
'use strict';

'use strict';

console.log('Index.js loaded');
console.log('Current directory:', process.cwd());
console.log('Script directory:', __dirname);

try {
    const inquirer = require('inquirer');
    console.log('Inquirer loaded successfully');
} catch (error) {
    console.error('Failed to load inquirer:', error);
}

try {
    const { loadFavorites } = require('./favorites');
    console.log('Favorites module loaded successfully');
} catch (error) {
    console.error('Failed to load favorites module:', error);
}

const inquirer = require('inquirer');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const chalk = require('chalk');
const { loadFavorites, saveFavorites, manageFavorites } = require('./favorites');

/**
 * Detects the package manager used in the current project
 * @returns {string} The detected package manager command (npm, yarn, pnpm)
 */
function detectPackageManager() {
    const cwd = process.cwd();

    if (fs.existsSync(path.join(cwd, 'pnpm-lock.yaml'))) {
        return 'pnpm';
    } else if (fs.existsSync(path.join(cwd, 'yarn.lock'))) {
        return 'yarn';
    } else {
        return 'npm';
    }
}

/**
 * Loads scripts from package.json
 * @returns {Object|null} The scripts object or null if not found
 */
function loadScripts() {
    const cwd = process.cwd();
    const packageJsonPath = path.join(cwd, 'package.json');

    try {
        if (fs.existsSync(packageJsonPath)) {
            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            return packageJson.scripts || {};
        }
    } catch (error) {
        console.error(chalk.red('Error reading package.json:'), error.message);
    }

    return null;
}

/**
 * Creates the choices array for the inquirer prompt
 * @param {Object} scripts - The scripts object from package.json
 * @param {Array} favorites - The array of favorite script names
 * @returns {Array} The choices array for inquirer
 */
function createChoices(scripts, favorites) {
    const scriptNames = Object.keys(scripts);

    if (scriptNames.length === 0) {
        return [];
    }

    const choices = [
        ...favorites.length > 0 ? [new inquirer.Separator(chalk.yellow('★ FAVORITES ★'))] : [],
        ...favorites.map(name => ({
            name: `${chalk.yellow('★')} ${chalk.green(name)}: ${chalk.dim(scripts[name])}`,
            value: name
        })),
        ...favorites.length > 0 ? [new inquirer.Separator(chalk.blue('ALL SCRIPTS'))] : [],
        ...scriptNames
            .filter(name => !favorites.includes(name))
            .map(name => ({
                name: `${chalk.green(name)}: ${chalk.dim(scripts[name])}`,
                value: name
            })),
        new inquirer.Separator(),
        {
            name: chalk.magenta('✎ Manage favorites...'),
            value: 'MANAGE_FAVORITES'
        },
        {
            name: chalk.red('✖ Exit'),
            value: 'EXIT'
        }
    ];

    return choices;
}

/**
 * Executes a script using the detected package manager
 * @param {string} scriptName - The name of the script to run
 * @param {string} packageManager - The package manager to use
 */
function executeScript(scriptName, packageManager) {
    const command = `${packageManager} run ${scriptName}`;
    console.log(chalk.blue(`\nExecuting: ${chalk.bold(command)}\n`));

    try {
        execSync(command, { stdio: 'inherit' });
        console.log(chalk.green('\n✓ Script completed successfully\n'));
    } catch (error) {
        console.error(chalk.red('\n✖ Script execution failed\n'));
    }
}

/**
 * Shows the main menu for script selection
 */
function showMainMenu() {
    const scripts = loadScripts();

    if (!scripts || Object.keys(scripts).length === 0) {
        console.error(chalk.red('No scripts found in package.json'));
        process.exit(1);
    }

    const packageManager = detectPackageManager();
    const favorites = loadFavorites();
    const choices = createChoices(scripts, favorites);

    inquirer
        .prompt([
            {
                type: 'list',
                name: 'scriptName',
                message: 'Select a script to run:',
                choices,
                pageSize: 15
            }
        ])
        .then(answers => {
            if (answers.scriptName === 'MANAGE_FAVORITES') {
                // Pass showMainMenu as the callback
                manageFavorites(scripts, showMainMenu);
                return;
            }

            if (answers.scriptName === 'EXIT') {
                console.log(chalk.blue('\nGoodbye! 👋\n'));
                process.exit(0);
            }

            executeScript(answers.scriptName, packageManager);
            showMainMenu(); // Continue the loop
        })
        .catch(error => {
            console.error(chalk.red('Error:'), error);
            process.exit(1);
        });
}

// Start the application
function main() {
    try {
        console.log(chalk.bold.blue('\n🚀 Taskr - Interactive Script Runner\n'));

        const scripts = loadScripts();

        if (!scripts || Object.keys(scripts).length === 0) {
            console.error(chalk.red('No scripts found in package.json'));
            return;
        }

        const packageManager = detectPackageManager();
        const favorites = loadFavorites();
        const choices = createChoices(scripts, favorites);

        console.log(chalk.blue(`\nTaskr - Using ${chalk.bold(packageManager)}\n`));

        inquirer
            .prompt([
                {
                    type: 'list',
                    name: 'scriptName',
                    message: 'Select a script to run:',
                    choices,
                    pageSize: 15
                }
            ])
            .then(answers => {
                // Handle the selection...
            })
            .catch(error => {
                console.error(chalk.red('Error in prompt:'), error);
            });
    } catch (error) {
        console.error(chalk.red('Error in main function:'), error);
    }
}

// Check if this file is being run directly
// Explicitly call main at the end of the file
console.log('Calling main function...');
    main();

module.exports = {
    main,
    showMainMenu,
    loadScripts,
    detectPackageManager
};
