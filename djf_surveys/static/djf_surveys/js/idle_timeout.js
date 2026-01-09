function initialise_timeout() {
  ["click", "touchstart", "mousemove", "scroll"].forEach((evt) =>
    document.removeEventListener(evt, initialise_timeout, false),
  );

  let idleTimeout;
  let countdownTimeout;
  let countdownInterval;
  const idleDurationSecs = parseInt(
    document.getElementById("link_back_on_cancel").dataset.timeout,
  ); // Use this line to change the total time a user has until redirected
  const countdownDurationSecs = parseInt(
    document.getElementById("link_back_on_cancel").dataset.dialogTimeout,
  ); // Use this line to how many seconds should remain for your pop-up to come up
  const redirectUrl = encodeURI(
    document.getElementById("link_back_on_cancel").dataset.link,
  ); // ADD URL TO WHICH YOU WANT TO REDIRECT USERS
  const popup = document.getElementById("idle-popup");
  const countdownElement = document.getElementById("countdown");
  const stayButton = document.getElementById("stay-btn");

  countdownElement.textContent = toString(countdownDurationSecs);

  const resetIdleTimeout = function () {
    if (idleTimeout) clearTimeout(idleTimeout);
    if (countdownTimeout) clearTimeout(countdownTimeout);
    if (countdownInterval) clearInterval(countdownInterval);
    popup.style.display = "none";
    countdownElement.textContent = countdownDurationSecs.toString();
    idleTimeout = setTimeout(showPopup, idleDurationSecs * 1000);
  };

  const showPopup = function () {
    popup.style.display = "block";
    let remainingSeconds = countdownDurationSecs;
    const updateCountdown = function () {
      countdownElement.textContent = remainingSeconds;
      if (remainingSeconds <= 0) {
        clearInterval(countdownInterval);
        location.href = redirectUrl;
        return;
      }
      remainingSeconds--;
    };
    countdownInterval = setInterval(updateCountdown, 1000);
  };

  stayButton.addEventListener("click", resetIdleTimeout, false);

  // Init on page load
  resetIdleTimeout();

  // Reset the idle timeout on any of the events listed below
  ["click", "touchstart", "mousemove", "scroll"].forEach((evt) =>
    document.addEventListener(evt, resetIdleTimeout, false),
  );
}

(function () {
  const popup = document.getElementById("idle-popup");
  popup.style.display = "none";
  ["click", "touchstart", "mousemove", "scroll"].forEach((evt) => {
    document.addEventListener(evt, initialise_timeout, false);
  });
})();
