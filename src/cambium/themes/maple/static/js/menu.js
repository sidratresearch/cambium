function openMenu() {
  const openIcon = document.getElementById("open-icon");
  const closeIcon = document.getElementById("close-icon");
  openIcon.classList.add("hidden");
  closeIcon.classList.remove("hidden");
  document.addEventListener("scroll", closeMenu);
  document.addEventListener("click", closeMenuIfClickedOutside);
}

function closeMenu() {
  const openIcon = document.getElementById("open-icon");
  const closeIcon = document.getElementById("close-icon");
  openIcon.classList.remove("hidden");
  closeIcon.classList.add("hidden");
  document.removeEventListener("scroll", closeMenu);
  document.removeEventListener("click", closeMenuIfClickedOutside);
}

function closeMenuIfClickedOutside(event) {
  const header = document.getElementsByTagName("header")[0];
  const menuPanel = document.getElementById("menu-panel");
  if (!menuPanel.contains(event.target) & !header.contains(event.target)) {
    menuPanel.classList.add("hidden");
    closeMenu();
  }
}

export function attachMenuButtonListener() {
  const menuButton = document.getElementById("menu-button");

  menuButton.addEventListener("click", () => {
    const menuPanel = document.getElementById("menu-panel");
    const result = menuPanel.classList.toggle("hidden");
    result ? closeMenu() : openMenu();
  });
}

export function themeToggle() {
  const toggle = document.getElementById("mode-toggle");
  const body = document.body;
  const logo = document.getElementById("built-with-cambium");
  const imageLight =
    "Built%20With%20Cambium%20-%20Green%20on%20Transparent.svg";
  const imageDark = "builtwithcambiumyellow.svg";

  toggle.addEventListener("change", function () {
    if (this.checked) {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("theme", "dark");
      body.dataset.pfTheme = "dark";
      // line here to change out the 'built with cambium' image
      const basepath = getBasePathFromPath(logo.src);
      logo.src = basepath + imageDark;
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
      body.dataset.pfTheme = "light";
      // line here to change out the 'built with cambium' image
      const basepath = getBasePathFromPath(logo.src);
      logo.src = basepath + imageLight;
    }
  });

  // check for saved user preference, if any, on load of the website
  document.addEventListener("DOMContentLoaded", (event) => {
    const theme = localStorage.getItem("theme");

    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      toggle.checked = true;
      body.dataset.pfTheme = "dark";
      // line here to change out the 'built with cambium' image
      const basepath = getBasePathFromPath(logo.src);
      logo.src = basepath + imageDark;
    }
  });
}

function getBasePathFromPath(path) {
  const lastSlash = path.lastIndexOf("/");
  const lastBackslash = path.lastIndexOf("\\");
  const lastSeparatorIndex = Math.max(lastSlash, lastBackslash);

  return lastSeparatorIndex === -1
    ? path
    : path.slice(0, lastSeparatorIndex + 1);
}
