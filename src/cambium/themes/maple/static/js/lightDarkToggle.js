// Light/Dark Mode Switching
import { cambiumToggleLightDark } from "./lightDark.js";

// Light dark toggle
export function attachLightDarkToggleListener() {
  const toggle = document.getElementById("light-dark-toggle");

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
