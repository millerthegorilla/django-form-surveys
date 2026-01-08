(function(){
    controls = document.getElementsByClassName('multiselect')
    let names = [];
    Array.from(controls).forEach(function (element) {
        if (names.indexOf(element.name) == '-1')
        {
            names.push(element.name)
        }
    });
    const form = document.getElementsByTagName('form')[0];
    form.addEventListener('submit', function(event) {
        event.preventDefault();
    }) 
})();
