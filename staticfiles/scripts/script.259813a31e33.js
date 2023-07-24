window.onload = function() {
    const navbarHeight = document.querySelector('.navbar').offsetHeight;
    document.getElementById('body-content').style.setProperty('--navbar-height', `${navbarHeight}px`);
  };