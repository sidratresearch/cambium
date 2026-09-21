/*
 * Main JS file for Cambium's Maple theme
 * Note that this sits on top of the root theme, and uses the root tableSorting.js file
 */
import { addSortingFunctionToAllTables } from "./tableSorting.js";
import { attachMenuButtonListener } from "./menu.js";
import { lightDarkToggle } from "./lightDark.js";

// Adding Sortable Nature to all Tables
addSortingFunctionToAllTables();

// Adding event listener to menu button
attachMenuButtonListener();

lightDarkToggle();

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
