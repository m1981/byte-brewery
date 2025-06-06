#!/usr/bin/env node
const inquirer = require('inquirer');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Get the directory where the script is located
const scriptDir = __dirname;

// Read package.json from the same directory as the script
const packageJsonPath = path.join(scriptDir, 'package.json');
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const scripts = packageJson.scripts || {};

// Path to favorites file
const favoritesPath = path.join(scriptDir, '.favorites');

// Read favorites file if it exists
let favorites = [];
try {
    if (fs.existsSync(favoritesPath)) {
        favorites = fs.readFileSync(favoritesPath, 'utf8')
            .split('\n')
            .filter(line => line.trim() && scripts[line.trim()]);
    }
} catch (error) {
    console.warn('Could not read favorites file:', error.message);
}

// Get all script names
const scriptNames = Object.keys(scripts);

if (scriptNames.length === 0) {
    console.log('No scripts found in package.json');
    process.exit(0);
}

// Create choices for inquirer with favorites at the top
const choices = [
    ...favorites.length > 0 ? [new inquirer.Separator('--- FAVORITES ---')] : [],
    ...favorites.map(name => ({
        name: `★ ${name}: ${scripts[name]}`,
        value: name
    })),
    ...favorites.length > 0 ? [new inquirer.Separator('--- ALL SCRIPTS ---')] : [],
    ...scriptNames
        .filter(name => !favorites.includes(name))
        .map(name => ({
            name: `${name}: ${scripts[name]}`,
            value: name
        })),
    new inquirer.Separator(),
    {
        name: '✎ Manage favorites...',
        value: 'MANAGE_FAVORITES'
    }
];

// Function to run the main menu
function showMainMenu() {
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
                showFavoritesMenu();
                return;
            }

            const command = `pnpm run ${answers.scriptName}`;
            console.log(`\nExecuting: ${command}\n`);

            try {
                execSync(command, { stdio: 'inherit', cwd: scriptDir });
            } catch (error) {
                console.error('Script execution failed');
            }

            // Return to the menu after script execution
            console.log('\nReturning to script menu...\n');
            showMainMenu();
        });
}

// Function to manage favorites
function showFavoritesMenu() {
    const allScripts = Object.keys(scripts);

    inquirer
        .prompt([
            {
                type: 'checkbox',
                name: 'selectedFavorites',
                message: 'Select your favorite scripts:',
                choices: allScripts.map(name => ({
                    name: `${name}: ${scripts[name]}`,
                    value: name,
                    checked: favorites.includes(name)
                })),
                pageSize: 15
            }
        ])
        .then(answers => {
            // Update favorites
            favorites = answers.selectedFavorites;

            // Save to file
            fs.writeFileSync(favoritesPath, favorites.join('\n'));

            console.log('\nFavorites updated successfully!\n');

            // Rebuild choices with new favorites
            choices.length = 0;
            choices.push(
                ...favorites.length > 0 ? [new inquirer.Separator('--- FAVORITES ---')] : [],
                ...favorites.map(name => ({
                    name: `★ ${name}: ${scripts[name]}`,
                    value: name
                })),
                ...favorites.length > 0 ? [new inquirer.Separator('--- ALL SCRIPTS ---')] : [],
                ...allScripts
                    .filter(name => !favorites.includes(name))
                    .map(name => ({
                        name: `${name}: ${scripts[name]}`,
                        value: name
                    })),
                new inquirer.Separator(),
                {
                    name: '✎ Manage favorites...',
                    value: 'MANAGE_FAVORITES'
                }
            );

            // Return to main menu
            showMainMenu();
        });
}

// Start the application
showMainMenu();

