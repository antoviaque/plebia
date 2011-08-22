//
// Copyright (C) 2011 Xavier Antoviaque <xavier@antoviaque.org>
//
// Part of this file are Copyright (C) Loic Dachary <loic@dachary.org>
// (Card Stories & Poker Source)
//
// This software's license gives you freedom; you can copy, convey,
// propagate, redistribute and/or modify this program under the terms of
// the GNU Affero Gereral Public License (AGPL) as published by the Free
// Software Foundation (FSF), either version 3 of the License, or (at your
// option) any later version of the AGPL published by the FSF.
//
// This program is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
// General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program in a file in the toplevel directory called
// "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
//

// Helpers //////////////////////////////////////////////////////////

module("plebia");

var plebia_default_setTimeout = $.plebia.setTimeout;
var plebia_default_setInterval = $.plebia.setInterval;
var plebia_default_ajax = $.plebia.ajax;
var plebia_default_error = $.plebia.error;

var mockjax_default_id = null;

function setup() {
    $.plebia.setTimeout = function(cb, delay) { return window.setTimeout(cb, delay); };
    $.plebia.setInterval = function(cb, delay) { return window.setInterval(cb, delay); };
    $.plebia.ajax = function(o) { throw o; };
    $.plebia.error = plebia_default_error;

    // Mockjax config & reset
    $.mockjaxSettings.responseTime = 10;
    $.mockjaxClear();
}

// Helpers: Mockjax ///////////////////////////////////////

function set_default_mockjax() {
    // Add a default answer (error) at the end of the mockjax answers list
    mockjax_default_id = $.mockjax({
        url: '*',
        status: 410,
        response: function() {
            start();
            ok(false, "API called on non-mocked URL");
            throw new Error("API called on non-mocked URL");
        }
    });
}

function unset_default_mockjax() {
    // Remove the default ajax answer (necessary before adding new answers)

    $.mockjaxClear(mockjax_default_id);
}

function mockjax_post_list() {
    // List of posts
    return $.mockjax({
        url: '/api/v1/post/?limit=50',
        responseText: {
            "meta": {"limit": 50, "next": null, "offset": 0, "previous": null, "total_count": 1},
            "objects": [{
                "date_added": "2011-08-21T20:03:21.301192", 
                "episode": "/api/v1/seriesseasonepisode/2/", 
                "id": "1", 
                "resource_uri": "/api/v1/post/1/"
            }]
        }
    });
}

function mockjax_post() {
    // Post
    return $.mockjax({
        url: '/api/v1/post/1/',
        responseText: {
            "date_added": "2011-08-21T20:03:21.301192", 
            "episode": "/api/v1/seriesseasonepisode/1/", 
            "id": "1", 
            "resource_uri": "/api/v1/post/1/"
        }
    });
}

function mockjax_episode() {
    // Episode
    return $.mockjax({
        url: '/api/v1/seriesseasonepisode/1/',
        responseText: {
            "date_added": "2011-08-21T20:03:13.738521", 
            "id": "1", 
            "name": "", 
            "number": 10, 
            "resource_uri": "/api/v1/seriesseasonepisode/1/", 
            "season": "/api/v1/seriesseason/1/", 
            "torrent": "/api/v1/torrent/1/", 
            "video": null
        }
    });
}

function mockjax_season() {
    // Season
    return $.mockjax({
        url: '/api/v1/seriesseason/1/',
        responseText: {
            "date_added": "2011-08-21T20:03:13.732927", 
            "id": "1", 
            "number": 4, 
            "resource_uri": "/api/v1/seriesseason/1/", 
            "series": "/api/v1/series/1/", 
            "torrent": null
        }
    });
}

function mockjax_series() {
    // Series
    return $.mockjax({
        url: '/api/v1/series/1/',
        responseText: {
            "date_added": "2011-08-21T20:03:13.720468", 
            "id": "1", 
            "name": "Test series", 
            "resource_uri": "/api/v1/series/1/"
        }
    });
}


// Tests ////////////////////////////////////////////////////////////


// STATE: searching ///////////////////////////////////
test("state_searching", function() {
    // QUnit init
    setup();
    stop();
    expect(17);
    
    var root = $('.plebia');
    var stream = $('.plebia_stream', root);

    // Mock API calls
    var mockjax_post_list_id = mockjax_post_list();
    var mockjax_post_id = mockjax_post();
    var mockjax_episode_id = mockjax_episode();
    var mockjax_season_id = mockjax_season();
    var mockjax_series_id = mockjax_series();

    // Torrent
    var mockjax_torrent_id = $.mockjax({
        url: '/api/v1/torrent/1/',
        responseText: {
            "date_added": "2011-08-22T17:26:17.403509", 
            "download_speed": "", 
            "eta": "", 
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
            "id": "1", 
            "name": "", 
            "peers": 25, 
            "progress": 0.0, 
            "resource_uri": "/api/v1/torrent/1/", 
            "seeds": 845, 
            "status": "New", 
            "type": "episode", 
            "upload_speed": ""
        }
    });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    $.plebia.refresh_stream(stream, root).done(function() {
        start();

        // Post <div>
        var post_dom = $('.plebia_post', stream);
        equal(post_dom.length, 1, "should have 1 post <div>");
        ok(post_dom.hasClass('plebia_post_searching'), 'wrong state');
        ok(post_dom.hasClass('plebia_post_update'), "post isn't marked to be updated");

        // API URLs
        equal($('.plebia_post_api_id', post_dom).val(), '/api/v1/post/1/');
        equal($('.plebia_episode_api_id', post_dom).val(), '/api/v1/seriesseasonepisode/1/');
        equal($('.plebia_season_api_id', post_dom).val(), '/api/v1/seriesseason/1/');
        equal($('.plebia_series_api_id', post_dom).val(), '/api/v1/series/1/');
        equal($('.plebia_torrent_api_id', post_dom).val(), '/api/v1/torrent/1/');
        equal($('.plebia_video_api_id', post_dom).val(), '');

        // Title
        equal($('.plebia_post_title', post_dom).html(), 'Test series - Season 4, Episode 10');

        // Next episode
        equal($('.plebia_next_episode .plebia_name', post_dom).val(), 'Test series');
        equal($('.plebia_next_episode .plebia_season_nb', post_dom).val(), '4');
        equal($('.plebia_next_episode .plebia_episode_nb', post_dom).val(), '11');

        // Second run of update should give same results
        stop();
        $.plebia.refresh_stream(stream, root).done(function() {
            start();

            var post_dom = $('.plebia_post', stream);
            equal(post_dom.length, 1, "should have 1 post <div>");
            ok(post_dom.hasClass('plebia_post_searching'), 'wrong state');
            ok(post_dom.hasClass('plebia_post_update'), "post isn't marked to be updated");
            equal($('.plebia_post_api_id', post_dom).val(), '/api/v1/post/1/');
        });
    });
});


// STATE: downloading (0%) ////////////////////////////
test("state_downloading_start1", function() {
    // QUnit init
    setup();
    stop();
    expect(15);
    
    var root = $('.plebia');
    var stream = $('.plebia_stream', root);

    // Mock API calls
    var mockjax_post_list_id = mockjax_post_list();
    var mockjax_post_id = mockjax_post();
    var mockjax_episode_id = mockjax_episode();
    var mockjax_season_id = mockjax_season();
    var mockjax_series_id = mockjax_series();

    // Torrent
    $.mockjax({
        url: '/api/v1/torrent/1/',
        responseText: {
            "date_added": "2011-08-22T18:54:30.333440", 
            "download_speed": "0.0 KiB/s", 
            "eta": "", 
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
            "id": "1", 
            "name": "", 
            "peers": 25, 
            "progress": 0.0, 
            "resource_uri": "/api/v1/torrent/1/", 
            "seeds": 862, 
            "status": "Downloading", 
            "type": "episode", 
            "upload_speed": "0.0 KiB/s"
        }
    });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    $.plebia.refresh_stream(stream, root).done(function() {
        start();

        // Post <div>
        var post_dom = $('.plebia_post', stream);
        equal(post_dom.length, 1, "should have 1 post <div>");
        ok(post_dom.hasClass('plebia_post_downloading'), 'wrong state');
        ok(post_dom.hasClass('plebia_post_update'), "post isn't marked to be updated");

        // API URLs
        equal($('.plebia_video_api_id', post_dom).val(), '');

        // Download information
        equal($('.plebia_info_msg', post_dom).html(), 'Video found! Starting download...');
        equal($('.plebia_percent', post_dom).html(), '0');
        equal($('.plebia_eta', post_dom).html(), '');
        ok($('.plebia_progress_bar', post_dom).hasClass('ui-progressbar'));
        equal($('.plebia_progress_bar', post_dom).attr('aria-valuenow'), '0');
        equal($('.plebia_torrent_name .plebia_value', post_dom).html(), '');
        equal($('.plebia_torrent_type .plebia_value', post_dom).html(), 'episode');
        equal($('.plebia_torrent_seeds .plebia_value', post_dom).html(), '862');
        equal($('.plebia_torrent_peers .plebia_value', post_dom).html(), '25');
        equal($('.plebia_torrent_upload_speed .plebia_value', post_dom).html(), '0.0 KiB/s');
        equal($('.plebia_torrent_download_speed .plebia_value', post_dom).html(), '0.0 KiB/s');
    });
});


// STATE: downloading (0.2%) ////////////////////////////
test("state_downloading_start2", function() {
    // QUnit init
    setup();
    stop();
    expect(10);
    
    var root = $('.plebia');
    var stream = $('.plebia_stream', root);

    // Mock API calls
    var mockjax_post_list_id = mockjax_post_list();
    var mockjax_post_id = mockjax_post();
    var mockjax_episode_id = mockjax_episode();
    var mockjax_season_id = mockjax_season();
    var mockjax_series_id = mockjax_series();

    // Torrent
    $.mockjax({
        url: '/api/v1/torrent/1/',
        responseText: {
            "date_added": "2011-08-22T18:54:30.333440", 
            "download_speed": "33.6 KiB/s", 
            "eta": "1h 28m", 
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
            "id": "1", 
            "name": "Test S04E10.avi", 
            "peers": 25, 
            "progress": 0.28000000000000003, 
            "resource_uri": "/api/v1/torrent/1/", 
            "seeds": 862, 
            "status": "Downloading", 
            "type": "episode", 
            "upload_speed": "10.0 KiB/s"
        }
    });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    $.plebia.refresh_stream(stream, root).done(function() {
        start();

        // Post <div>
        var post_dom = $('.plebia_post', stream);
        equal(post_dom.length, 1, "should have 1 post <div>");
        ok(post_dom.hasClass('plebia_post_downloading'), 'wrong state');
        ok(post_dom.hasClass('plebia_post_update'), "post isn't marked to be updated");

        // API URLs
        equal($('.plebia_video_api_id', post_dom).val(), '');

        // Download information
        equal($('.plebia_info_msg', post_dom).html(), 'Video found! Starting download...');
        equal($('.plebia_percent', post_dom).html(), '0.28');
        equal($('.plebia_eta', post_dom).html(), '1h 28m');
        equal($('.plebia_torrent_name .plebia_value', post_dom).html(), 'Test S04E10.avi');
        equal($('.plebia_torrent_upload_speed .plebia_value', post_dom).html(), '10.0 KiB/s');
        equal($('.plebia_torrent_download_speed .plebia_value', post_dom).html(), '33.6 KiB/s');
    });
});

// STATE: downloading (15%) ////////////////////////////
test("state_downloading", function() {
    // QUnit init
    setup();
    stop();
    expect(1);
    
    var root = $('.plebia');
    var stream = $('.plebia_stream', root);

    // Mock API calls
    var mockjax_post_list_id = mockjax_post_list();
    var mockjax_post_id = mockjax_post();
    var mockjax_episode_id = mockjax_episode();
    var mockjax_season_id = mockjax_season();
    var mockjax_series_id = mockjax_series();

    // Torrent
    $.mockjax({
        url: '/api/v1/torrent/1/',
        responseText: {
            "date_added": "2011-08-22T18:54:30.333440", 
            "download_speed": "1.0 MiB/s", 
            "eta": "2m 27s", 
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
            "id": "1", 
            "name": "Test S04E10.avi", 
            "peers": 25, 
            "progress": 15.23, 
            "resource_uri": "/api/v1/torrent/1/", 
            "seeds": 862, 
            "status": "Downloading", 
            "type": "episode", 
            "upload_speed": "0.0 KiB/s"
        }
    });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    $.plebia.refresh_stream(stream, root).done(function() {
        start();

        // Info message has changed
        var post_dom = $('.plebia_post', stream);
        equal($('.plebia_info_msg', post_dom).html(), 'Downloading...');
    });
});


// STATE: downloading (99.9%) ////////////////////////////
test("state_downloading_end", function() {
    // QUnit init
    setup();
    stop();
    expect(1);
    
    var root = $('.plebia');
    var stream = $('.plebia_stream', root);

    // Mock API calls
    var mockjax_post_list_id = mockjax_post_list();
    var mockjax_post_id = mockjax_post();
    var mockjax_episode_id = mockjax_episode();
    var mockjax_season_id = mockjax_season();
    var mockjax_series_id = mockjax_series();

    // Torrent
    $.mockjax({
        url: '/api/v1/torrent/1/',
        responseText: {
            "date_added": "2011-08-22T18:54:30.333440", 
            "download_speed": "26.4 KiB/s", 
            "eta": "1s", 
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
            "id": "1", 
            "name": "Test S04E10.avi", 
            "peers": 25, 
            "progress": 99.980000000000004, 
            "resource_uri": "/api/v1/torrent/1/", 
            "seeds": 862, 
            "status": "Downloading", 
            "type": "episode", 
            "upload_speed": "484.3 KiB/s"
        }
    });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    $.plebia.refresh_stream(stream, root).done(function() {
        start();

        // Info message has changed
        var post_dom = $('.plebia_post', stream);
        equal($('.plebia_info_msg', post_dom).html(), 'Finishing download...');
    });
});


// STATE: downloading (100%) ////////////////////////////
test("state_downloading_completed", function() {
    // QUnit init
    setup();
    stop();
    expect(2);
    
    var root = $('.plebia');
    var stream = $('.plebia_stream', root);

    // Mock API calls
    var mockjax_post_list_id = mockjax_post_list();
    var mockjax_post_id = mockjax_post();
    var mockjax_episode_id = mockjax_episode();
    var mockjax_season_id = mockjax_season();
    var mockjax_series_id = mockjax_series();

    // Torrent
    $.mockjax({
        url: '/api/v1/torrent/1/',
        responseText: {
            "date_added": "2011-08-22T18:54:30.333440", 
            "download_speed": "8.0 KiB/s", 
            "eta": "0s", 
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 
            "id": "1", 
            "name": "Test S04E10.avi", 
            "peers": 25, 
            "progress": 100.0, 
            "resource_uri": "/api/v1/torrent/1/", 
            "seeds": 862, 
            "status": "Completed", 
            "type": "episode", 
            "upload_speed": "0.0 KiB/s"
        }
    });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    $.plebia.refresh_stream(stream, root).done(function() {
        start();

        var post_dom = $('.plebia_post', stream);
        // Still no video API object - remain in downloading state
        ok(post_dom.hasClass('plebia_post_downloading'), 'wrong state');
        equal($('.plebia_info_msg', post_dom).html(), 'Finishing download...');
    });
});





// Helper hooks tests /////////////////////////////////////

test("error", function() {
    setup();
    expect(1);

    var alert = window.alert;
    window.alert = function(err) { equal(err, 'an error occurred', 'calls window.alert on error'); };
    $.plebia.error('an error occurred');
    window.alert = alert;
  });

test("setTimeout", function() {
  expect(2);

  $.plebia.setTimeout = plebia_default_setTimeout;

  var setTimeout = $.plebia.window.setTimeout;
  $.plebia.window.setTimeout = function(cb, delay) {
    equal(cb, 'a function');
    equal(delay, 42);
  };

  $.plebia.setTimeout('a function', 42);
  $.plebia.window.setTimeout = setTimeout;
});

test("setInterval", function() {
  expect(2);

  $.plebia.setInterval = plebia_default_setInterval;

  var setInterval = $.plebia.window.setInterval;
  $.plebia.window.setInterval = function(cb, delay) {
    equal(cb, 'a function');
    equal(delay, 42);
  };

  $.plebia.setInterval('a function', 42);
  $.plebia.window.setInterval = setInterval;
});

test("xhr_error", function() {
    expect(1);

    $.plebia.error = function(err) { equal(err, 'an xhr error occurred', 'calls $.plebia.error'); };
    $.plebia.xhr_error({xhr: 'object'}, 500, 'an xhr error occurred');
});

test("onbeforeunload", function() {
    setup();
    expect(1);

    $(window).trigger('beforeunload');
    equal($.plebia.error, $.plebia.noop, 'error handler gets set to a noop function on beforeunload');
});

