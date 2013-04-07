var savedPlaces = [];
$(function() {

   $("#SearchTerm").keyup(function(event) {
      if (event.keyCode == 13) {
        mapSearch($(this).val());
      }
   });

   $("#mapname").keyup(function(event) {
       if (event.keyCode == 13) {
           info = {name: $(this).val() };
           $.ajax({
               url: '/Maps/',
               data: JSON.stringify(info),
               type: 'POST',
               success: function(msg, respStatus, request) {
                   if (request.status == 201) {
                       window.location.href = request.getResponseHeader('Location');
                   }
               },
               error: function(msg, respStatus, request) {
                   //409 == conflict
                   //Which in this case means the map name already exists
                   //so just navigate there
                   if (msg.status == 409) {
                       window.location.href = 'Maps/' + info.name;
                   }
               }
           });

       }
   });

   $("#PlacesList").on("click", ".place", function() {
       var currPlace = savedPlaces[$(this).data('placeId')];
       selectPlace(currPlace);
   });

   $("#PlacesList").on("click", ".DeletePlace", function(evt) {

      evt.cancelBubble = true;
      if (evt.stopPropagation) {
          evt.stopPropagation();
      }
      var parentPlace = $(this).parents('.place');
      $.ajax({
         url:'Places/'+parentPlace.data('placeId') + '/',
         type:'DELETE',
         success: function() {
             Map.deletePlace(savedPlaces[parentPlace.data('placeId')]);
             parentPlace.remove();
         }
      });
   });

});

function selectPlace(place) {
    $(".Selected").removeClass("Selected");
    $("#"+place.docId).addClass('Selected');
    Map.center(place);
}
function initMapView() {
    $.each(savedPlaces, function() {
        addPlace(this);
    });

    SetupPlaceNameEditor();

    Map.initialize($("#map-canvas")[0]);
    Map.setPlaces(savedPlaces, function(place) {
        selectPlace(place);
    });
    Map.fitPlaces();
}

function addPlace(place) {
    //appendTo doesn't like leading/trailing whitespace in the html
    savedPlaces[place.id] = place;
    place.docId = 'Place'+place.id;
    var html = tmpl("place_template", place).trim();
    var elem = $(html).appendTo($("#PlacesList"));
    elem.data('placeId', place.id);
    Map.addPlace(place, function(place) {
        selectPlace(place);
    });
}

function mapSearch(searchTerm)
{
   $('.Selected').removeClass('Selected');
   Map.search(searchTerm, function(result) {
       var newItem = {name: result.formatted_address, lat: result.geometry.location.lat(), lng: result.geometry.location.lng(), address: result.formatted_address};
       Map.addPlace(result, function(place) {
           selectPlace(place);
       });
       $.ajax({
           url: 'Places',
           type: 'POST',
           data: JSON.stringify(newItem),
           success: function(msg) {
               //Should we get the id from the msg
               //or do another RT to GET it?
               newItem.id = msg.id;
               addPlace(newItem);
           }
       });
   });
}

function SetupPlaceNameEditor() {
    $("#PlacesList").on('click', '.name', function() {
      var input = $('<input />', {'type': 'text', 'name': 'NameEdit', 'value': $(this).html()});
      $(this).hide();
      $(this).parent().append(input);
      input.focus();
   });

   $("#PlacesList").on('blur', 'input', function(evt) {
      $(this).siblings(".name").show();
      var newName = $(this).val();
      $(this).siblings(".name").html(newName);
      var placeId = $(this).parents('.place').data('placeId');
      $.ajax({
         url:'Places/'+placeId+'/',
         data: JSON.stringify({name: newName}),
         type:'PUT',
      });
      $(this).remove();
   });

   $("#PlacesList").on('keydown', 'input', function(evt) {
      if (evt.keyCode === undefined || evt.keyCode == 13) {
            $(this).blur();
            return;
      }
   });
}
