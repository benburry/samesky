$(document).ready(function () {
  chrome.storage.sync.get({
    endpoint_url: 'http://home.burry.name:5000'
  }, function(items) {
    var baseurl = items.endpoint_url;
    $.ajaxSetup({ cache: false });
    var tz = jstz.determine();

    if (typeof (tz) !== 'undefined') {
        tz_name = tz.name();

        var update = function() {
            $.getJSON(baseurl + '/getpics/' + tz_name, function(data) {
                if (data.me.img) {
                    img = new Image();
                    img.onload = function () {
                        $('#tz').html(data.me.display_tz);
                        $('#time').html(data.me.time);

                        $('html').css('background', "url('" + img.src + "') no-repeat center center fixed");
                        $('html').css('-webkit-background-size', 'cover');
                    };
                    img.src = baseurl + data.me.img;
                }
            });
        };
    }
    update();
    setInterval(update, 60000);
  });
});
