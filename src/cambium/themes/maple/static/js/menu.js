function openMenu() {
  const menuPanel = document.getElementById("menu-panel");
  menuPanel.classList.add("menu-active");
  document.addEventListener("scroll", closeMenu);
  document.addEventListener("click", closeMenuIfClickedOutside);
}

function closeMenu() {
  const menuPanel = document.getElementById("menu-panel");
  menuPanel.classList.remove("menu-active");
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
  const menuButtonOpen = document.getElementById("menu-open-button");
  const menuButtonClose = document.getElementById("menu-close-button");

  menuButtonOpen.addEventListener("click", () => {
    openMenu();
  });
  menuButtonClose.addEventListener("click", () => {
    closeMenu();
  });
}
