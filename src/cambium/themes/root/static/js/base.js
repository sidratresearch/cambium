import { addSortingFunctionToAllTables } from "./tableSorting.js";
import { attachMenuButtonListener, themeToggle } from "./menu.js";

// Adding Sortable Nature to all Tables
addSortingFunctionToAllTables();

// Adding event listener to menu button
attachMenuButtonListener();

// Add theme toggle listener
themeToggle();
