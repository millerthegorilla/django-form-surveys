const widgets = document.getElementsByClassName("widget-attrs-id")
const variables = {};
function initRatingStars(widgetAttrsId) {
    variables[`ratingStars_${ widgetAttrsId }`] = [...document.getElementById(`parent_start_${widgetAttrsId}`).getElementsByClassName("rating__star")];

    function executeRating(stars) {
        variables[`starClassActive_${ widgetAttrsId }`] = "rating__star rating_active";
        variables[`starClassUnactive_${ widgetAttrsId }`] = "rating__star rating_inactive";
        variables[`starsLength_${ widgetAttrsId }`] = stars.length;
        let i;

        stars.map((star) => {
            star.onclick = () => {
                i = stars.indexOf(star);
                if (star.className.indexOf(variables[`starClassUnactive_${ widgetAttrsId }`]) !== -1) {
                    for (i; i >= 0; --i) stars[i].className = variables[`starClassActive_${ widgetAttrsId }`];
                } else {
                    for (i; i < variables[`starsLength_${ widgetAttrsId }`]; ++i) stars[i].className = variables[`starClassUnactive_${ widgetAttrsId }`];
                }
                variables[`ratingStarsActive_${ widgetAttrsId }`] = [...document.getElementById(`parent_start_${ widgetAttrsId }`).getElementsByClassName("rating_active")];
                variables[`hiddenInput_${ widgetAttrsId }`] = document.getElementById(`${ widgetAttrsId }`);
                variables[`hiddenInput_${ widgetAttrsId }`].value = variables[`ratingStarsActive_${ widgetAttrsId }`].length;
            };
        });

    }

    executeRating(variables[`ratingStars_${ widgetAttrsId }`]);
}

for (const widget of widgets) {
    initRatingStars(widget.dataset.id);
}