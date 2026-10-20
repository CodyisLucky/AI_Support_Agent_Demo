(function () {
  var root = document.documentElement;
  var pill = document.querySelector(".bar");
  if (!pill) return;

  var THRESHOLD = 8;
  var desktop = window.matchMedia("(min-width: 761px)");
  var ticking = false;

  function measure() {
    if (!desktop.matches) {
      pill.style.removeProperty("--nav-sticky-w");
      return;
    }
    var wasTop = root.classList.contains("nav-at-top");
    root.classList.add("nav-measuring");
    root.classList.remove("nav-at-top");
    pill.style.removeProperty("--nav-sticky-w");
    var row = pill.querySelector(".bar-row");
    var rowStyles = getComputedStyle(row);
    var gap = parseFloat(rowStyles.columnGap) || 0;
    var pad = (parseFloat(rowStyles.paddingLeft) || 0) + (parseFloat(rowStyles.paddingRight) || 0);
    var kids = row.children;
    var inner = pad;
    for (var i = 0; i < kids.length; i++) inner += kids[i].scrollWidth;
    if (kids.length > 1) inner += gap * (kids.length - 1);
    var border = pill.offsetWidth - pill.clientWidth;
    pill.style.setProperty("--nav-sticky-w", Math.ceil(inner + border) + "px");
    if (wasTop) root.classList.add("nav-at-top");
    void pill.offsetWidth;
    root.classList.remove("nav-measuring");
  }

  function apply() {
    root.classList.toggle("nav-at-top", window.scrollY <= THRESHOLD);
    ticking = false;
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(apply);
  }

  measure();
  apply();
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      root.classList.add("nav-anim");
    });
  });

  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
  window.addEventListener("load", measure);
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(measure, 150);
  });
  window.addEventListener("scroll", onScroll, { passive: true });
})();
