(function () {
  const toast = document.getElementById("added-toast");
  if (!toast) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hide = () => {
    if (toast.dataset.leaving) return;
    if (reduce) { toast.remove(); return; }
    toast.dataset.leaving = "true";
    const done = () => toast.remove();
    toast.addEventListener("transitionend", done, { once: true });
    setTimeout(done, 240);
  };
  toast.querySelector(".toast-close").addEventListener("click", hide);
  setTimeout(hide, 4500);
})();
