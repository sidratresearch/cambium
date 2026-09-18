/*
 * Main JS file for Cambium's Maple theme
 * Note that this sits on top of the root theme, and uses the root tableSorting.js file
 */
import { addSortingFunctionToAllTables } from "./tableSorting.js";
import { attachMenuButtonListener } from "./menu.js";

// Adding Sortable Nature to all Tables
addSortingFunctionToAllTables();

// Adding event listener to menu button
attachMenuButtonListener();
