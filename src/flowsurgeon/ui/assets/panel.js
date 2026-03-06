(function () {
  "use strict";

  var root = document.getElementById("fs-root");
  if (!root) return;

  var toggleBtn = document.getElementById("fs-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      root.classList.toggle("fs-collapsed");
      toggleBtn.textContent = root.classList.contains("fs-collapsed") ? "▲" : "▼";
    });
  }
})();
