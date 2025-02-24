// get menu and btn and apply drop down
const menu = document.getElementById("menu");
const menuBtn = document.getElementById("menuBtn");

menuBtn.addEventListener("click", () => {
   menu.classList.toggle("open");
});
