/*
 * Main JS file for Cambium's Maple theme
 * Note that this sits on top of the root theme, and uses the root tableSorting.js and lightDark.js files
 */
import { addSortingFunctionToAllTables } from "./tableSorting.js";
import { attachMenuButtonListener } from "./menu.js";
import { attachLightDarkToggleListener } from "./lightDarkToggle.js";
import { cambiumInitializeLightDark } from "./lightDark.js";

// Adding Sortable Nature to all Tables
addSortingFunctionToAllTables();

// Adding event listener to menu button
attachMenuButtonListener();

// Set what the theme should be on first load
cambiumInitializeLightDark();

// Add a listener to the switcher
attachLightDarkToggleListener();

// Back to top button
function backToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function attachBackToTopListener() {
  const button = document.getElementById("back-to-top-button");

  button.addEventListener("click", () => {
    backToTop();
  });
}

attachBackToTopListener();
