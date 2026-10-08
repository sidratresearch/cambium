const menuPanel = document.getElementById("menu-panel");
const screenShadeDiv = document.getElementById("screen-shade");
const inertElements = document.querySelectorAll("[data-inert-in-menu]");

function closeOnEsc(event) {
  if (event.key === "Escape") {
    closeMenu();
  }
}

function openMenu() {
  menuPanel.classList.toggle("menu-active");
  screenShadeDiv.classList.toggle("screen-shade-active");
  screenShadeDiv.addEventListener("click", closeMenu);
  inertElements.forEach((element) => element.setAttribute("inert", true));
  window.addEventListener("keydown", closeOnEsc);
}

function closeMenu() {
  menuPanel.classList.toggle("menu-active");
  screenShadeDiv.classList.toggle("screen-shade-active");
  screenShadeDiv.removeEventListener("click", closeMenu);
  inertElements.forEach((element) => element.removeAttribute("inert"));
  window.removeEventListener("keydown", closeOnEsc);
}

export function attachMenuButtonListener() {
  const menuButtonOpen = document.getElementById("menu-open-button");
  const menuButtonClose = document.getElementById("menu-close-button");

  menuButtonOpen.addEventListener("click", () => {
    openMenu();
  });
  menuButtonClose.addEventListener("click", () => {
    closeMenu();
  });
}
