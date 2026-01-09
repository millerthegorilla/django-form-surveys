(function () {
    const TIMEOUT_SECONDS = 15; // 15 seconds
    const REDIRECT_URL = document.getElementById("link_back_on_success_page").dataset.link;
    const MESSAGE = document.getElementById("link_back_on_success_page").dataset.msg;
    let timeRemaining = TIMEOUT_SECONDS;

    // Show countdown
    const countdownElement = document.createElement("p");
    countdownElement.id = "countdown";
    countdownElement.className = "mt-4 text-sm text-gray-600 font-semibold";
    document.querySelector("#timerbox").appendChild(countdownElement);

    function updateCountdown() {
      const mins = Math.floor(timeRemaining / 60);
      const secs = timeRemaining % 60;
      countdownElement.textContent = `${MESSAGE} ${mins}:${secs.toString().padStart(2, "0")}`;

      timeRemaining--;
      if (timeRemaining < 0) {
        window.location.href = REDIRECT_URL;
      }
    }

    updateCountdown();
    setInterval(updateCountdown, 1000);
  })();