// Light/Dark Mode Switching
export function cambiumToggleLightDark(mode = null) {
  //   Swaps Light and/or dark
  const body = document.body;
  if (!mode) {
    const mode = document.documentElement.getAttribute("data-theme");
  }

  if (mode === "light") {
    // Swap to light
    document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem("theme", "light");
    body.dataset.pfTheme = "light";
  } else if (mode === "dark") {
    // Swap to dark
    document.documentElement.setAttribute("data-theme", "dark");
    body.dataset.pfTheme = "dark";
    localStorage.setItem("theme", "dark");
  }
}

export function cambiumInitializeLightDark() {
  // Reads info from local storage about light/dark
  const theme = localStorage.getItem("theme");
  // Swaps theme
  cambiumToggleLightDark(theme);

  //   make sure toggle is checked if dark mode
  if (theme === "dark") {
    const toggle = document.getElementById("light-dark-toggle");
    toggle.checked = true;
  }
}

// Light dark toggle
export function lightDarkToggle() {
  const toggle = document.getElementById("light-dark-toggle");

  toggle.addEventListener("change", function () {
    if (this.checked) {
      cambiumToggleLightDark("dark");
    } else {
      cambiumToggleLightDark("light");
    }
  });

  cambiumInitializeLightDark();
}
