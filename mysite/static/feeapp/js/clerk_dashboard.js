document.addEventListener('DOMContentLoaded', function() {
 
  document.querySelectorAll(".grid .card").forEach(card => {
    card.addEventListener("click", function (event) {
      
      if (this.getAttribute('href')) {
        return; 
      }
      
      event.preventDefault();
      const title = this.querySelector("h3").innerText.trim();
      handleClick(title);
    });
  });
});

function handleClick(moduleName) {
  if (moduleName === 'Design Challan') {
    window.location.href = '/challan-form/';  
  } 
   else if (moduleName === 'Manage Installments') {
  window.location.href = '/manage-installment/';  
  } else if (moduleName === 'Update Challan') {
    window.location.href = '/update_challan/';
  } 
  else if (moduleName === 'Search Challan') {
    window.location.href = '/search_challan/';
  }
  else if (moduleName === 'Logout') {
    window.location.href = '/logout/';
  }
  else if (moduleName === 'Report / History') {
    window.location.href = '/challan-summary/';
  } else {
    alert(moduleName + " Clicked");
  }
}