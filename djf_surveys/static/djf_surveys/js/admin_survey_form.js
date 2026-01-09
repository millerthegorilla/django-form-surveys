(function () {
  var section_field_id_gdpr_compliant = document.getElementById(
    "section_field_id_gdpr_compliant",
  );
  var id_can_anonymous_user = document.getElementById("id_can_anonymous_user");
  if (id_can_anonymous_user.checked) {
    section_field_id_gdpr_compliant.style.display = "list-item";
  } else {
    section_field_id_gdpr_compliant.style.display = "none";
  }
  if (id_can_anonymous_user) {
    id_can_anonymous_user.addEventListener("change", function () {
      if (this.checked) {
        section_field_id_gdpr_compliant.style.display = "list-item";
      } else {
        section_field_id_gdpr_compliant.style.display = "none";
      }
    });
  }
})();
