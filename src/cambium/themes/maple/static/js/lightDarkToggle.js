// Light/Dark Mode Switching
import { cambiumToggleLightDark } from "./lightDark.js";

// Light dark toggle
export function attachLightDarkToggleListener() {
  const button = document.getElementById("light-dark-toggle-button");

  button.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    // set the theme to whatever is NOT currently in use
    if (currentTheme === "light") {
      cambiumToggleLightDark("dark");
    } else {
      cambiumToggleLightDark("light");
    }
  });
}
