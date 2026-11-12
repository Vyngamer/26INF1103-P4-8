// code to open the sidebar
const menuButton = document.querySelector('.menu-btn');
const sidebar = document.querySelector('.sidebar');
const scrim = document.querySelector('.scrim');

function setMenuOpen(open) {
  sidebar.classList.toggle('open', open);
  scrim.classList.toggle('show', open);
  menuButton.setAttribute('aria-expanded', open);
}

menuButton.addEventListener('click', () => setMenuOpen(!sidebar.classList.contains('open')));
scrim.addEventListener('click', () => setMenuOpen(false));


function sendToChatbot(userText) {
	$.ajax({

	})
}
