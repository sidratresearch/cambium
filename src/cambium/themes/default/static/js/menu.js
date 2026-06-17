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
