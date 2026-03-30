const moduleBoxLogoutBtn = document.getElementById('logoutBoxBtn');
function confirmLogout(event) {
    event.preventDefault();
    const userConfirmed = confirm("Are you sure you want to log out?");
    
    if (userConfirmed) {
        window.location.href = event.target.href.replace('logout_confirmation', 'logout_action');
    }
}
if (moduleBoxLogoutBtn) {
    moduleBoxLogoutBtn.addEventListener('click', confirmLogout);
}
