// Light/Dark Mode Switching
export function cambiumToggleLightDark(mode = null) {
  //   Swaps Light and/or dark
  const body = document.body;
  if (!mode) {
    const mode = document.documentElement.getAttribute("data-theme");
  }

  if (mode == "dark") {
    // Swap to light
    document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem("theme", "light");
    body.dataset.pfTheme = "light";
  } else if (mode == "light") {
    // Swap to dark
    document.documentElement.setAttribute("data-theme", "dark");
    body.dataset.pfTheme = "dark";
    localStorage.setItem("theme", "dark");
  }
}

export function cambiumInitializeLightDark() {
  const body = document.body;
  // Reads info from local storage about light/dark
  const theme = localStorage.getItem("theme");
  // Swaps theme
  cambiumToggleLightDark(theme);
}
