function openMenu() {
  const menuPanel = document.getElementById("menu-panel");
  menuPanel.classList.remove("hidden");
  document.addEventListener("scroll", closeMenu);
  document.addEventListener("click", closeMenuIfClickedOutside);
}

function closeMenu() {
  const menuPanel = document.getElementById("menu-panel");
  menuPanel.classList.add("hidden");
  document.removeEventListener("scroll", closeMenu);
  document.removeEventListener("click", closeMenuIfClickedOutside);
}

function closeMenuIfClickedOutside(event) {
  const header = document.getElementsByTagName("header")[0];
  const menuPanel = document.getElementById("menu-panel");
  if (!menuPanel.contains(event.target) & !header.contains(event.target)) {
    closeMenu();
  }
}

export function attachMenuButtonListener() {
  const menuButtonOpen = document.getElementById("menu-button-open");
  const menuButtonClose = document.getElementById("menu-button-close");

  menuButtonOpen.addEventListener("click", () => {
    openMenu();
  });
  menuButtonClose.addEventListener("click", () => {
    closeMenu();
  });
}

export function themeToggle() {
  const toggle = document.getElementById("mode-toggle");
  const body = document.body;

  toggle.addEventListener("change", function () {
    if (this.checked) {
      body.classList.add("dark-theme");
      localStorage.setItem("darkMode", "enabled");
      body.dataset.pfTheme = "dark";
    } else {
      body.classList.remove("dark-theme");
      localStorage.setItem("darkMode", "disabled");
      body.dataset.pfTheme = "light";
    }
  });

  // check for saved user preference, if any, on load of the website
  document.addEventListener("DOMContentLoaded", (event) => {
    const darkMode = localStorage.getItem("darkMode");

    if (darkMode === "enabled") {
      body.classList.add("dark-theme");
      toggle.checked = true;
      body.dataset.pfTheme = "dark";
    }
  });
}
