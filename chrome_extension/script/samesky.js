$(document).ready(function () {
  var menotyou = true;
  var datacache;


  chrome.storage.sync.get({
    endpoint_url: 'http://home.burry.name:5000',
    address: 'London',
  }, function(items) {
    var baseurl = items.endpoint_url;
    var address = items.address;

    $.ajaxSetup({ cache: false });

    var render = function() {
        if (datacache) {
            var whichdata = menotyou ? datacache.me : datacache.you;
            if (whichdata.img) {
                img = new Image();
                img.onload = function () {
                    console.log('onload');
                    console.log(whichdata);
                    $('#tz').html(whichdata.display_tz + '&nbsp;&nbsp;' + whichdata.temp.c + '&deg;C/' + whichdata.temp.f + '&deg;F');
                    $('#time').html(whichdata.time);

                    $('html').css('background', "url('" + img.src + "') no-repeat center center fixed");
                    $('html').css('-webkit-background-size', 'cover');
                };
                img.src = baseurl + whichdata.img;
            }
        }
    };

    var update = function() {
        $.getJSON(baseurl + '/samesky/' + address, function(data) {
            console.log('render');
            datacache = data;
            render();
        });
    };

    $("#time").click(function() {
        menotyou = !menotyou;
        render();
    });

    update();
    setInterval(update, 60000);
  });

});
