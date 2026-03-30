if (window.history && window.history.replaceState) {
   
    window.history.replaceState({ page: 'role_select' }, '', window.location.href);
    
    window.history.pushState({ page: 'role_select' }, '', window.location.href);

    window.addEventListener('popstate', function(e) {
       
        window.history.pushState({ page: 'role_select' }, '', window.location.href);
    });
}

function goToLogin() {
    const role = document.getElementById("roleSelect").value;
    if (role === "Student") {
        window.location.replace("/challan/login/");
    } else if (role === "Clerk") {
        window.location.replace("/challan/clerk/login/");
    } else {
        alert("Please Select a role.");
    }
}