(function () {
  controls = document.querySelectorAll(".multiselect-parent, .rating-parent");
  let names = [];
  Array.from(controls).forEach(function (element) {
    if (names.indexOf(element.name) == "-1") {
      names.push(element.name);
      let html_insert = `<div id="popup-wrapper"><div id="error-popup-${element.name}" class="error-popup"><span class="popuptext" id="popuptext">You need to select at least one option</span></div></div>`;
      let select_form = document.getElementById("id-" + element.name + '-hidden');
      select_form.insertAdjacentHTML("afterend", html_insert);
    }
  });
  const form = document.getElementsByTagName("form")[0];
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    let valid = false;
    for (let value of names) {
      valid = false;
      let el = document.getElementById("id_" + value + '-parent');
      if (document.getElementsByClassName(`${value}`)[0].dataset.required == "False") {
        valid = true;
        continue;
      }
      if (el.classList.contains("rating-parent")) 
      {
        let stars = document.getElementById(`parent_start_id_${value}`).querySelectorAll(".rating_active");
        if (stars.length > 0) {
          valid = true;
          continue;
        }
      }
      else if (el.classList.contains("multiselect-parent"))
      {
        let checkboxes = document.getElementsByName(value);
        for (const checkbox of checkboxes) {
          if (checkbox.checked) {
            valid = true;
            continue;
          }
        }
      }

      let popup = document.getElementById("error-popup-" + value);
      if (!valid) {
        //show popup
        popup.classList.toggle("show-popup");
        popup
          .scrollIntoView({ behavior: "smooth", block: "center" });
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
