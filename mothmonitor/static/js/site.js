function hiddenChildren(ev) {
  if (ev.target.closest(".hide-children")) {
    return
  }
  children = this.querySelectorAll(".hide-children") || this.children;
  children.forEach((el) => {
    el.classList.toggle("hidden-children");
  })
}
document.addEventListener("DOMContentLoaded", (event) => {
  document.querySelectorAll(".hide-children-control").forEach((el) => {
    el.onclick = hiddenChildren.bind(el);
  })
});
