(function () {
  controls = document.getElementsByClassName("multiselect");
  let names = [];
  Array.from(controls).forEach(function (element) {
    if (names.indexOf(element.name) == "-1") {
      names.push(element.name);
      let html_insert = `<div id="popup-wrapper"><div id="error-popup-${element.name}" class="error-popup"><span class="popuptext" id="popuptext">You need to select at least one option</span></div></div>`;
      let select_form = document.getElementById("id_" + element.name);
      select_form.insertAdjacentHTML("afterend", html_insert);
    }
  });
  const form = document.getElementsByTagName("form")[0];
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    let valid = false;
    for (let value of names) {
      valid = false;
      //if a checkbox with this name is checked then valid = true and break
      let checkboxes = document.getElementsByName(value);
      for (const checkbox of checkboxes) {
        if (checkbox.checked) {
          valid = true;
          break;
        }
      }

      let popup = document.getElementById("error-popup-" + value);
      if (!valid) {
        //show popup
        popup.classList.toggle("show-popup");
        document
          .getElementById("id_" + value)
          .scrollIntoView({ behavior: "smooth" });
        setTimeout(function () {
          popup.classList.toggle("show-popup");
        }, 3000);
        break;
      }
    }
    if (valid) {
      form.submit();
    }
  });
})();
