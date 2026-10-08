// Light/Dark Mode Switching
import { cambiumToggleLightDark } from "./lightDark.js";

// Light dark toggle
export function attachLightDarkToggleListener() {
  const toggle = document.getElementById("light-dark-toggle");
  const label = document.querySelector('label[for="light-dark-toggle"]');

  // the label is what's tab-focusable, not the checkbox
  // so if the label is tab-focused, we need to listen for keyboard events
  label.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle.checked = !toggle.checked;
      toggle.dispatchEvent(new Event("change"));
    }
  });

  toggle.addEventListener("change", function () {
    // set the theme to whatever is NOT currently in use
    const currentTheme = document.documentElement.getAttribute("data-theme");
    if (currentTheme === "light") {
      cambiumToggleLightDark("dark");
    } else {
      cambiumToggleLightDark("light");
    }
  });
}
