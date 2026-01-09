const cancelButton = document.getElementById("cancel_button");

cancelButton.addEventListener("click", function (event) {
  event.preventDefault();
  const indexLink = document.getElementById("index-link").dataset.link;
  window.location.href = indexLink;
});