var Map = (function() {
    var my = {};

    var geocoder;
    var map;
    var searchMarker;
    var infoWindow;
    var savedPlaces;
    var placeImage;
    var placeShadow;

    my.initialize = function (mapObj) {
        geocoder = new google.maps.Geocoder();
        var latlng = new google.maps.LatLng(37.09024, -95.712891);
        var mapOptions = {
            zoom: 3,
            center: latlng,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: false,
        }
        map = new google.maps.Map(mapObj, mapOptions);
        searchMarker = new google.maps.Marker({
                map: map});
        infoWindow = new google.maps.InfoWindow;
        google.maps.event.addListener(map, 'click', function() {
            infoWindow.close();
        });

        //Taken from http://stackoverflow.com/questions/7095574/google-maps-api-3-custom-marker-color-for-default-dot-marker
        var pinColor = "0000FF";
        placeImage = new google.maps.MarkerImage("http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|" + pinColor,
            new google.maps.Size(21, 34),
            new google.maps.Point(0,0),
            new google.maps.Point(10, 34));
        placeShadow = new google.maps.MarkerImage("http://chart.apis.google.com/chart?chst=d_map_pin_shadow",
            new google.maps.Size(40, 37),
            new google.maps.Point(0, 0),
            new google.maps.Point(12, 35));
    };

    function showInfoWindow(marker, saveCallback)
    {
        var link = document.createElement('a');
        link.href = 'javascript:void(0)';
        link.onclick = function() {
            infoWindow.close();
            searchMarker.setMap(null);
            if (saveCallback !== undefined) {
                saveCallback();
            }
        }
        link.innerHTML = 'Save';
        infoWindow.setContent(link);
        infoWindow.open(map, marker);
        $("#savePlace").click(function() {
        });
    }

    my.search = function (searchTerm, saveCallback) {
        infoWindow.close();
        geocoder.geocode( { 'address': searchTerm }, function(results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                map.setCenter(results[0].geometry.location);
                map.fitBounds(results[0].geometry.viewport);

                searchMarker.setMap(map);
                searchMarker.setPosition(results[0].geometry.location);
                google.maps.event.addListener(searchMarker, 'click', function() {
                    showInfoWindow(this, saveCallback.bind(undefined, results[0]));
                });
            } else {
                searchMarker.setMap(null);
            }
        });
    }

    my.deletePlace = function(place) {
        if (place.marker) {
            place.marker.setMap(null);
            place.marker = undefined;
        }
    }

    my.addPlace = function(place, selectedCallback) {
        place.marker = new google.maps.Marker({
            map: map,
            position: new google.maps.LatLng(place.lat, place.lng),
            icon: placeImage,
            shadow: placeShadow,
        });
        google.maps.event.addListener(place.marker, 'click', function(mark) {
            selectedCallback(place);
        });

    }

    my.editPlace = function(place) {
        my.deletePlace(place);
        my.addPlace(place);
    }

    function forEachPlace(fun) {
        if (savedPlaces !== undefined) {
            for (var k in savedPlaces) {
                if (savedPlaces.hasOwnProperty(k)) {
                    fun(savedPlaces[k]);
                }
            }
        }
    }
    my.setPlaces = function (places, selectedCallback) {
        forEachPlace(function(place) {
            my.deletePlace(place);
        });

        savedPlaces = places;
        forEachPlace(function(place) {
            my.addPlace(place, selectedCallback);
        });
    }

    my.deletePlace = function(place) {
        savedPlaces[place.id].marker.setMap(null);
        savedPlaces[place.id] = undefined;
    }

    my.center = function(place) {
        map.setCenter(new google.maps.LatLng(place.lat, place.lng));
        map.setZoom(15);
    }

    my.fitPlaces = function() {
        var currBounds = new google.maps.LatLngBounds();
        var placeAdded = false;
        forEachPlace(function(place) {
            placeAdded = true;
            currBounds.extend(new google.maps.LatLng(place.lat, place.lng));
        });
        if (placeAdded) {
            map.fitBounds(currBounds);
        }
    }

    return my;
}());
