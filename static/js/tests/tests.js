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

var plebia_default_stream_update_loop = $.plebia.Stream.prototype.update_loop;
var plebia_default_season_update_loop = $.plebia.Season.prototype.update_loop;

var mockjax_default_id = null;

function setup() {
    $.plebia.Stream.prototype.update_loop = function(){};
    $.plebia.Season.prototype.update_loop = function(){};

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

// Tests ////////////////////////////////////////////////////////////


// STATE: searching ///////////////////////////////////
test("stream_init", function() {
    // QUnit init
    setup();
    stop();
    expect(17);
    
    var plebia_dom = $('.plebia');
    var stream_dom = $('.plebia_stream', plebia_dom);

    // Mock API requests
    var mockjax_post_id = $.mockjax({ url: '/api/v1/post/?limit=50', proxy: 'mocks/stream_init_posts.json' });
    var mockjax_season_id = $.mockjax({ url: '/api/v1/season/1/', proxy: 'mocks/stream_init_season.json' });
    var mockjax_torrent_id = $.mockjax({ url: '/api/v1/torrent/1/', proxy: 'mocks/stream_init_torrent_new.json' });

    // Don't let any other AJAX requests go through
    set_default_mockjax();

    // Init & refresh stream based on above ajax calls
    var plebia = new $.plebia.Plebia(plebia_dom);
    $.when(plebia.init()).done(function() {
        start();

        var post_dom = $('.plebia_post', stream_dom);
        var series_dom = $('.plebia_series', post_dom);

        equal(post_dom.length, 1, "should have 1 post <div>");

        // API URLs
        equal(stream_dom.children('input.plebia_api_url').val(), '/api/v1/post/?limit=50');
        equal(post_dom.children('input.plebia_api_url').val(), '/api/v1/post/1/');
        equal(series_dom.children('input.plebia_api_url').val(), '/api/v1/series/2/');

        // Title
        equal($('.plebia_content_right .plebia_name', series_dom).html(), 'Pioneer One');

        // Retreive seasons & episodes
        stop();
        var deferred1 = $.Deferred();
        $.when(series_dom[0].series.load_season_list()).done(function() {
            start();

            var season_dom = $('.plebia_season', series_dom);
            var episode_1_dom = $('.plebia_episode:eq(0)', season_dom);
            var episode_2_dom = $('.plebia_episode:eq(1)', season_dom);

            equal(season_dom.length, 1, "should have 1 season <div>");

            // API URLs
            equal(season_dom.children('input.plebia_api_url').val(), '/api/v1/season/1/');
            equal(episode_1_dom.children('input.plebia_api_url').val(), '/api/v1/episode/1/');
            equal(episode_2_dom.children('input.plebia_api_url').val(), '/api/v1/episode/2/');

            // Episode state
            ok(episode_1_dom.hasClass('plebia_state_searching'));
            ok(episode_2_dom.hasClass('plebia_state_not_started'));

            // Title
            equal($('.plebia_title', episode_1_dom).html(), 'Earthfall');
            equal($('.plebia_title', episode_2_dom).html(), 'The Man From Mars');

            // Launch a watchbox
            stop();
            $.when(episode_1_dom[0].episode.on_click()).done(function() {
                deferred1.resolve();
            });
        });

        // Watchbox
        $.when(deferred1).done(function() {
            start();

            var watchbox_dom = $('#fancybox-content .plebia_watchbox');

            equal(watchbox_dom.length, 1, "should have 1 watchbox <div>");
            ok(watchbox_dom.hasClass('plebia_state_searching'));
            equal($('.plebia_series_title', watchbox_dom).html(), 'Pioneer One');
            ok($('.plebia_state .plebia_info', watchbox_dom).html().indexOf("Searching for video...") != -1, 'Wrong content for this state');
        });
    });
});



