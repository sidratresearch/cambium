function onMenuToggle(menuPanel) {
  menuPanel.classList.toggle("hidden");
}

export function attachMenuButtonListener() {
  const menuButtonOpen = document.getElementById("menu-button-open");
  const menuButtonClose = document.getElementById("menu-button-close");
  const menuPanel = document.getElementById("menu-panel");

  menuButtonOpen.addEventListener("click", () => {
    onMenuToggle(menuPanel);
  });
  menuButtonClose.addEventListener("click", () => {
    onMenuToggle(menuPanel);
  });
}
