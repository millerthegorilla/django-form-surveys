(function(){
   const content = document.getElementById('survey-content');
   const currentHeight = content.offsetHeight;
   const currentWidth = content.offsetWidth;
   var multiplierH = 0
   var multiplierW = 0
   if (currentHeight < screen.height)
   {
       multiplierH = currentHeight / screen.height;
   }
   else
   {
       multiplierH = screen.height / currentHeight;
   }
   content.style.zoom = multiplierH;
})();