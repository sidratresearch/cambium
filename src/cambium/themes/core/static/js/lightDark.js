// Light/Dark Mode Switching
export function cambiumToggleLightDark(mode, setLocalStorage = true) {
  //   Swaps Light and/or dark mode, destination is whatever was passed
  const body = document.body;

  document.documentElement.setAttribute("data-theme", mode);
  body.dataset.pfTheme = mode; // set the theme for Pagefind

  // on the first load, don't save a user preference
  // but save that preference when the theme changes from a user action
  if (setLocalStorage) {
    localStorage.setItem("theme", mode);
  }
}

export function cambiumInitializeLightDark() {
  // Reads info from local storage about light/dark
  let theme = localStorage.getItem("theme");

  // use the website default if nothing in localstorage
  if (!theme) {
    theme = document.documentElement.getAttribute("data-theme");
  }

  // Swaps theme, but since this is the first load, don't set localstorage
  cambiumToggleLightDark(theme, false);
}
