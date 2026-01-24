(function () {

    const TIMEOUT_SECONDS = document.getElementById("screensaver-data").dataset.timeout;
    
    console.log("Screensaver timeout seconds:", TIMEOUT_SECONDS);
    const scsaver = new Scsaver('#scsaver', defaults = {
        waitTime: TIMEOUT_SECONDS * 1000,
        events: ['keydown', 'mousemove', 'touchstart', 'touchmove', 'click', 'scroll'],
        doInterval: 200,
        showFadeTime: 1000,
        hideFadeTime: 1000,
        autoStart: true,
        progressBar: false,
        progressBarParent: null,
        on: null,
        debug: false,
    });

    const textElement = document.getElementById('scsaver-text');
    let posX = 50;
    let posY = 50;
    let dirX = 2; // Horizontal speed and direction
    let dirY = 2; // Vertical speed and direction
    const speed = 0.4;

    function animate() {
        // Get current dimensions of the viewport and the text element
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const textWidth = textElement.offsetWidth;
        const textHeight = textElement.offsetHeight;

        // Update positions
        posX += dirX * speed;
        posY += dirY * speed;

        // Check boundaries and reverse direction if needed
        // Horizontal boundaries
        if (posX + textWidth > viewportWidth || posX < 0) {
            dirX *= -1; // Reverse horizontal direction
        }

        // Vertical boundaries
        if (posY + textHeight > viewportHeight || posY < 0) {
            dirY *= -1; // Reverse vertical direction
        }

        // Apply new positions
        textElement.style.left = posX + 'px';
        textElement.style.top = posY + 'px';

        // Continue the animation loop
        requestAnimationFrame(animate);
    }

    // Optional: Recalculate dimensions on window resize for responsiveness
    window.addEventListener('resize', () => {
        // The dimensions are retrieved within the animate function, so no need for extra logic here
    });


    id = null;

    scsaver.on('showStart', function () {
        id = requestAnimationFrame(animate);
    });

    scsaver.on('hideStart', function () {
        cancelAnimationFrame(id);
    });

})();