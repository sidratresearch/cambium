const menuPanel = document.getElementById("menu-panel");
const screenShadeDiv = document.getElementById("screen-shade");

function openMenu() {
  menuPanel.classList.toggle("menu-active");
  screenShadeDiv.classList.toggle("screen-shade-active");
  screenShadeDiv.addEventListener("click", closeMenu);
}

function closeMenu() {
  menuPanel.classList.toggle("menu-active");
  screenShadeDiv.classList.toggle("screen-shade-active");
  screenShadeDiv.removeEventListener("click", closeMenu);
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
