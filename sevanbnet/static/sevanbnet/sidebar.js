// Keeps the control panel's sidebar open once it's opened (Unfold 0.108 to 0.110).
//
// Unfold's CSS puts the sidebar beside the page from 1280 px (Tailwind's xl), but its
// JavaScript treats 1280 px as a narrow window. It also closes the sidebar whenever the
// page's size changes on a narrow window. At exactly 1280 px, opening the sidebar narrows
// the page, a long page (Site settings, any edit page) grows taller, and the sidebar
// closes again at once. This wraps Unfold's theme() (app.js) so the sidebar uses the
// CSS breakpoint and only resets when the window crosses it.
//
// Loaded through UNFOLD["SCRIPTS"], which runs before app.js; Alpine fires alpine:init
// after app.js and before it evaluates x-data="theme(...)".
document.addEventListener("alpine:init", () => {
  const unfoldTheme = window.theme;
  const wide = window.matchMedia("(min-width: 80rem)");
  // Wide windows remember the sidebar (open unless closed before); narrow ones start closed.
  const remembered = () => wide.matches && localStorage.getItem("sidebarOpen") !== "0";

  window.theme = (...args) => {
    const data = unfoldTheme(...args);
    data.sidebarOpen = remembered();
    data.sidebarToggle = function () {
      this.sidebarOpen = !this.sidebarOpen;
      if (wide.matches) localStorage.setItem("sidebarOpen", this.sidebarOpen ? "1" : "0");
    };
    // Alpine's resize plugin has no .window modifier, so this watched <html>'s size.
    delete data.themeBindings["x-resize.window"];
    const unfoldInit = data.init;
    data.init = function () {
      unfoldInit.call(this);
      wide.addEventListener("change", () => {
        this.sidebarOpen = remembered();
      });
    };
    return data;
  };
});
