'use strict';

const inquirer = require('inquirer');
const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

/**
 * Gets the path to the favorites file
 * @returns {string} The path to the favorites file
 */
function getFavoritesPath() {
    return path.join(process.cwd(), '.taskr-favorites');
}

/**
 * Loads favorites from the .taskr-favorites file
 * @returns {Array} The array of favorite script names
 */
function loadFavorites() {
    const favoritesPath = getFavoritesPath();

    try {
        if (fs.existsSync(favoritesPath)) {
            const content = fs.readFileSync(favoritesPath, 'utf8');
            return content
                .split('\n')
                .map(line => line.trim())
                .filter(Boolean);
        }
    } catch (error) {
        console.warn(chalk.yellow('Could not read favorites file:'), error.message);
    }

    return [];
}

/**
 * Saves favorites to the .taskr-favorites file
 * @param {Array} favorites - The array of favorite script names
 */
function saveFavorites(favorites) {
    const favoritesPath = getFavoritesPath();

    try {
        fs.writeFileSync(favoritesPath, favorites.join('\n'));
    } catch (error) {
        console.error(chalk.red('Could not save favorites:'), error.message);
    }
}

/**
 * Shows the favorites management menu
 * @param {Object} scripts - The scripts object from package.json
 * @param {Function} callback - The function to call after managing favorites
 */
function manageFavorites(scripts, callback) {
    const favorites = loadFavorites();
    const scriptNames = Object.keys(scripts);

    inquirer
        .prompt([
            {
                type: 'checkbox',
                name: 'selectedFavorites',
                message: 'Select your favorite scripts:',
                choices: scriptNames.map(name => ({
                    name: `${name}: ${scripts[name]}`,
                    value: name,
                    checked: favorites.includes(name)
                })),
                pageSize: 15
            }
        ])
        .then(answers => {
            saveFavorites(answers.selectedFavorites);
            console.log(chalk.green('\n✓ Favorites updated successfully!\n'));

            if (typeof callback === 'function') {
                callback();
            }
        })
        .catch(error => {
            console.error(chalk.red('Error:'), error);

            if (typeof callback === 'function') {
                callback();
            }
        });
}

module.exports = {
    loadFavorites,
    saveFavorites,
    manageFavorites
};
