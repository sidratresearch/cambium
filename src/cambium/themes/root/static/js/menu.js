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

// export function attachMenuButtonListener() {
//   const menuButtonOpen = document.getElementById("menu-button-open");
//   const menuButtonClose = document.getElementById("menu-button-close");

//   menuButtonOpen.addEventListener("click", () => {
//     openMenu();
//   });
//   menuButtonClose.addEventListener("click", () => {
//     closeMenu();
//   });
// }
