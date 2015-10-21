$(document).ready(function () {
  var menotyou = true;
  var datacache;


  chrome.storage.sync.get({
    endpoint_url: 'http://home.burry.name:5000'
  }, function(items) {
    var baseurl = items.endpoint_url;
    $.ajaxSetup({ cache: false });
    var tz = jstz.determine();

    if (typeof (tz) !== 'undefined') {
        tz_name = tz.name();

        var render = function() {
            if (datacache) {
                var whichdata = menotyou ? datacache.me : datacache.you;
                if (whichdata.img) {
                    img = new Image();
                    img.onload = function () {
                        $('#tz').html(whichdata.display_tz);
                        $('#time').html(whichdata.time);

                        $('html').css('background', "url('" + img.src + "') no-repeat center center fixed");
                        $('html').css('-webkit-background-size', 'cover');
                    };
                    img.src = baseurl + whichdata.img;
                }
            }
        };

        var update = function() {
            $.getJSON(baseurl + '/getpics/' + tz_name, function(data) {
                datacache = data;
                render();
            });
        };

        $("#time").click(function() {
            menotyou = !menotyou;
            render();
        });
    }
    update();
    setInterval(update, 60000);
  });

});
