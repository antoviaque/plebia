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

// Plugin ///////////////////////////////////////////////////////////

(function($) {

    $.fn.plebia = function() {
        // Startup method - Invoked on the <div.plebia> root object
        // init objects and populate stream

        var plebia_dom = this;
        var plebia = new $.plebia.Plebia(plebia_dom);
        plebia.init();
    };

    /////////////////////////////////////////////////////////////////////////////////////
    // Classes //////////////////////////////////////////////////////////////////////////
    /////////////////////////////////////////////////////////////////////////////////////

    $.plebia = {};

    // Helpers //////////////////////////////////////////////////////////////////////////

    /**
     * Copies members from an object to another object.
     * @param {Object} target the object to be copied onto
     * @param {Object} source the object to copy from
     * @param {Boolean} deep  whether the copy is deep or shallow
     */
    $.plebia.extend = function(target, source, deep) {
        for (var i in source) {
            if (deep || Object.hasOwnProperty.call(source, i)) {
                target[i] = source[i];
            }
        }
        return target;
    }

    /**
     * Converts a number of seconds into either days, hours, minutes or seconds,
     * depending on which is the highest non-null
     * Take a pessimist bet (ie round to the higher value)
     */
    $.plebia.human_eta = function(seconds) {
        // Days
        if (seconds/(3600*24) >= 1) {
            var eta = Math.ceil(seconds/(3600*24)) + " days";
        }
        // Hours
        else if (seconds/3600 >= 1) {
            var eta = Math.ceil(seconds/3600) + " hours";
        }
        // Minutes
        else if (seconds/60 >= 1) {
            var eta = Math.ceil(seconds/60) + " minutes";
        }
        // Seconds
        else {
            var eta = Math.ceil(seconds) + " seconds";
        }
        return eta;
    }

    // BaseObject (parent of all objects) ///////////////////////////////////////////////

    $.plebia.BaseObject = function() {
        this.dom = null;
        this.window = window;
        this.location = location;
    };

    $.plebia.BaseObject.prototype.noop = function() {};

    $.plebia.BaseObject.prototype.error = function() { alert(error); };

    $.plebia.BaseObject.prototype.xhr_error = function(xhr, status, error) {
        this.error(error);
    };

    $.plebia.BaseObject.prototype.setTimeout = function(cb, delay) { 
        return this.window.setTimeout(cb, delay); 
    };

    $.plebia.BaseObject.prototype.setInterval = function(cb, delay) { 
        return this.window.setInterval(cb, delay); 
    };


    // APIObject (object with attributes from a REST API request) ///////////////////////

    $.plebia.APIObject = function() {
        this.api_obj = null;
        this.api_base_url = '/api/v1/';
    };

    // BaseObject inheritance
    $.plebia.APIObject.prototype = new $.plebia.BaseObject();
    $.plebia.APIObject.prototype.constructor = $.plebia.APIObject; 

    $.plebia.APIObject.prototype.api_set_url = function(api_url) {
        // Set the API URL on the DOM input field

        var $this = this;

        var input_dom = $this.dom.children('input.plebia_api_url');
        input_dom.val(api_url);
    };

    $.plebia.APIObject.prototype.api_get_url = function() {
        // Get the API URL stored on the DOM input field

        var $this = this;
        
        var input_dom = $this.dom.children('input.plebia_api_url');
        var api_url = input_dom.val();

        return api_url;
    };

    $.plebia.APIObject.prototype.api_load = function() {
        // Refresh API object from the server

        var $this = this;
        var deferred = $.Deferred();

        var api_url = $this.api_get_url();

        if(api_url) {
            // Get from server
            $.when($.getJSON(api_url)).done(function(obj) {
                // Store object
                $this.api_obj = obj;
                
                deferred.resolve();
            });
            return deferred.promise();
        } else {
            return {};
        }
    };


    // Plebia (root element) ////////////////////////////////////////////////////////////

    $.plebia.Plebia = function(dom) {
        dom[0].plebia = this;
        this.dom = dom;
    };

    // BaseObject inheritance
    $.plebia.Plebia.prototype = new $.plebia.BaseObject();
    $.plebia.Plebia.prototype.constructor = $.plebia.Plebia; 

    // init()
    $.plebia.Plebia.prototype.init = function() {
        var $this = this;
        var deferred = $.Deferred();

        // Display the stream
        var stream_dom = $('.plebia_stream', $this.dom);
        var stream = new $.plebia.Stream(stream_dom, $this.dom);
        $.when(stream.init()).done(function() {
            deferred.resolve();
        });

        // Dress buttons
        $('input:submit', $this.dom).button();

        // Load auto-suggest
        $('.plebia_header input.plebia_name', $this.dom).liveSearch({url: '/ajax/search/'});

        // Init WatchBox and attach to plebia DOM
        $this.dom[0].watchbox = new $.plebia.WatchBox($this.dom);

        // Add feedback tab
        var uv = document.createElement('script'); uv.type = 'text/javascript'; uv.async = true;
        uv.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'widget.uservoice.com/6PhXO6580egdGy3eefwsAg.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(uv, s);
        
        return deferred.promise();
    };


    // Stream ///////////////////////////////////////////////////////////////////////////

    $.plebia.Stream = function(dom, plebia_dom) {
        dom[0].stream = this;
        this.dom = dom;
        this.plebia_dom = plebia_dom;
    };

    // APIObject inheritance
    $.plebia.Stream.prototype = new $.plebia.APIObject();
    $.plebia.Stream.prototype.constructor = $.plebia.Stream; 

    $.plebia.Stream.prototype.init = function() {
        // Get info from API and populate stream

        var $this = this;
        var deferred = $.Deferred();

        // Attach object to API URL
        $this.api_set_url($this.api_base_url+'post/?limit=80');

        // Populate stream (all posts)
        $.when($this.add_new_posts()).done(function() {
            // Init completed
            deferred.resolve();

            // Start regular update
            $this.update_loop();
        });

        return deferred.promise();
    };

    $.plebia.Stream.prototype.add_new_posts = function(loaded_post_list, position) {
        // Add posts in API but not in DOM 

        var $this = this;
        var deferred = $.Deferred();

        // Optional args
        if(!loaded_post_list) {
            // If not provided, load all posts
            var loaded_post_list = new Array();
        }
        if(!position) {
            var position = 'bottom';
        }

        var new_post_list = new Array();
        var deferred_list = new Array();

        // Get object from API
        $.when($this.api_load()).done(function() {
            // Identify all posts that haven't been loaded yet
            for(i in $this.api_obj.objects) {
                var post_obj = $this.api_obj.objects[i];
                if($.inArray(post_obj.resource_uri, loaded_post_list) == -1) {
                    new_post_list.push(post_obj);
                }
            }

            // Load them
            var count = new_post_list.length;
            if(count == 0) {
                deferred.resolve();
            };
            $.each(new_post_list, function() {
                var post_obj = this;
                count--;

                // Add post to stream
                $this.add_post(post_obj, position);
                
                // When the last post has finished loading, we're done
                if(count == 0) {
                    deferred.resolve();
                };
            });
        });

        return deferred.promise();
    };

    $.plebia.Stream.prototype.add_post = function(api_post_obj, position) {
        var $this = this;

        // Add marker <div> where the post should be loaded
        var post_dom = $('<div></div>');
        if(position == 'top') {
            $this.dom.prepend(post_dom);
        } else {
            $this.dom.append(post_dom);
        }

        // Init post object using values already retreived from API
        var post = new $.plebia.Post(post_dom, $this.dom);
        post.init(api_post_obj);
    };

    $.plebia.Stream.prototype.create_post = function(series_id) {
        // Send a new post to the server to create it and update stream to show it

        var $this = this;
        var deferred = $.Deferred();

        // Create new post on server with series, add to stream
        $.getJSON('/ajax/newpost/'+series_id+'/', function(response) {
            $.when($this.update()).done(function() {
                deferred.resolve();
            });
        });
        
        return deferred.promise();
    },

    $.plebia.Stream.prototype.update_loop = function() {
        var $this = this;

        $this.update().done(function() {
            $this.setTimeout(function() {
                $this.update_loop();
            }, 2000);
        });
    };

    $.plebia.Stream.prototype.update = function() {
        var $this = this;
        var deferred = $.Deferred();

        var loaded_post_list = new Array();
        var elems = $('.plebia_post', $this.dom);
        var count = elems.length;

        // Load posts if there is no post yet
        if(count==0) {
            $this.add_new_posts(loaded_post_list, 'top').done(function() {
                deferred.resolve();
            });
        }

        // Look through posts that are already loaded
        elems.each(function() {
            var post_dom = $(this);
            var post_obj = $(this)[0].post;
            
            // Keep track of loaded posts ids to not reload them later on
            loaded_post_list.push(post_obj.api_get_url());

            // Refresh individual post
            var dfr1 = post_obj.update();

            if(!--count) { // at the last item
                var dfr2 = $this.add_new_posts(loaded_post_list, 'top');
                
                $.when(dfr1, dfr2).then(function() {
                    deferred.resolve();
                });
            }
        });

        return deferred.promise();
    };


    // Post /////////////////////////////////////////////////////////////////////////////

    $.plebia.Post = function(dom, stream_dom) {
        dom[0].post = this;
        this.dom = dom;
        this.stream_dom = stream_dom;
        this.plebia_dom = stream_dom[0].stream.plebia_dom;
    };

    // APIObject inheritance
    $.plebia.Post.prototype = new $.plebia.APIObject();
    $.plebia.Post.prototype.constructor = $.plebia.Post; 

    $.plebia.Post.prototype.init = function(api_post_obj) {
        // Populate post DOM with templates and values from API

        var $this = this;

        // Copy base template
        var content_template = $('.plebia_template .plebia_post_template', $this.plebia_dom).html();
        $this.dom.html(content_template);
        
        // Class name
        $this.dom.addClass('plebia_post');

        // Create series DOM & object using values already retreived from API
        var series_dom = $('.plebia_series', $this.dom);
        var series = new $.plebia.Series(series_dom, $this.dom);
        series.init(api_post_obj.series);

        // Populate post with actual data
        $this.load(api_post_obj);
    };

    $.plebia.Post.prototype.load = function(api_post_obj) {
        // Set the HTML values in the base template
        
        var $this = this;

        // Store API values without reloading them from API
        $this.api_obj = api_post_obj;
        $this.api_set_url(api_post_obj.resource_uri);

        // Update DOM
        $('.plebia_post_time', $this.dom).html(api_post_obj.date_added);
    };
    
    $.plebia.Post.prototype.update = function() {
        // Refresh content

        var $this = this;
        var deferred = $.Deferred();

        // Refresh contained series
        var series = $('.plebia_series', $this.dom)[0].series;
        $.when(series.update()).done(function() {
            deferred.resolve();
        });
        
        return deferred.promise();
    };

    // Series ///////////////////////////////////////////////////////////////////////////

    $.plebia.Series = function(dom, post_dom) {
        dom[0].series = this;
        this.dom = dom;
        this.post_dom = post_dom;
        this.stream_dom = post_dom[0].post.stream_dom;
        this.plebia_dom = post_dom[0].post.plebia_dom;
    };

    // APIObject inheritance
    $.plebia.Series.prototype = new $.plebia.APIObject();
    $.plebia.Series.prototype.constructor = $.plebia.Series;

    $.plebia.Series.prototype.init = function(api_series_obj) {
        // Populate post DOM with templates and values from API

        var $this = this;

        // Copy base template
        var content_template = $('.plebia_template .plebia_series_template', $this.plebia_dom).html();
        $this.dom.html(content_template);
        
        // Class name
        $this.dom.addClass('plebia_series');

        // API Object
        $this.api_set_url(api_series_obj.resource_uri);
        $this.api_obj = api_series_obj;

        // Populate post with actual data
        $this.load();

        // JS for opening/closing the episodes list
        $("a.plebia_trigger", $this.dom).click(function(){
            $(".plebia_menu_content", $this.dom).toggle("fast");
            $(this).toggleClass("plebia_active");
            
            if($(this).hasClass("plebia_active")) {
                $this.load_season_list();
            } else {
                $('.plebia_season_list', $this.dom).empty();
            }

            return false;
        });
    };

    $.plebia.Series.prototype.load = function(api_series_obj) {
        // Set the HTML values in the base template

        var $this = this;

        $('.plebia_poster', $this.dom).attr('src', encodeURI('/static/banner.php?file_path='+$this.api_obj.poster_url));
        $('.plebia_name', $this.dom).html($this.api_obj.name);
        $('.plebia_overview', $this.dom).html($this.api_obj.overview.substring(0,320));
    };

    $.plebia.Series.prototype.update = function() {
        // Refresh content

        var $this = this;
        var deferred = $.Deferred();

        // Refresh active season if tab is expanded
        var trigger_dom = $("a.plebia_trigger", $this.dom);
        var active_season_dom = $('.plebia_season.plebia_active', $this.dom);
        if(trigger_dom.hasClass("plebia_active") && active_season_dom.length > 0) {
            $.when(active_season_dom[0].season.update()).done(function() {
                deferred.resolve();
            });
        } else {
            deferred.resolve();
        }
        
        return deferred.promise();
    };

    $.plebia.Series.prototype.load_season_list = function() {
        // Get seasons list from API and add any new one to the DOM

        var $this = this;
        var deferred = $.Deferred();
        var deferred_list = new Array();
        var season_list_dom = $('.plebia_season_list', $this.dom);
        
        // Ajax loading notifier
        $('.plebia .plebia_preloader').show();

        // Seasons content
        var season_list = new Array();
        for(i in $this.api_obj.season_list) {
            var api_season_url = $this.api_obj.season_list[i];

            // Create season DOM (hidden to show only one at a time)
            var season_dom = $('<div></div>').hide();
            $('.plebia_season_list', $this.dom).append(season_dom);

            // Init season object, which populates the DOM using API call
            var season = new $.plebia.Season(season_dom, $this.dom);
            season_list.push(season);
            deferred_list.push(season.init(api_season_url));
        }

        // Wait until all seasons are loaded
        $.when.apply(window, deferred_list).done(function() {
            // Season selector
            $('.plebia_season_selector', $this.dom).empty();
            for(i in season_list) {
                var season = season_list[i].api_obj;

                // Separator
                if(i == 0) {
                    $('.plebia_season_selector', $this.dom).append('Season ');
                } else {
                    $('.plebia_season_selector', $this.dom).append(' - ');
                }

                // Link
                var season_link = $('<a href="javascript://">'+season.number+'</a>');
                season_link.addClass('plebia_season_'+season.number);
                season_link.click(function() {
                    var series_dom = $(this).parents('.plebia_series');
                    series_dom[0].series.select_season($(this).html());
                }); 
                $('.plebia_season_selector', $this.dom).append(season_link);
            }

            $this.select_season(1);

            // Ajax loading notifier
            $('.plebia .plebia_preloader').hide();

            deferred.resolve();
        });

        return deferred.promise();
    };

    $.plebia.Series.prototype.select_season = function(season_number) {
        // Change the active season

        var $this = this;

        // Show active season in selector
        $('.plebia_season_selector a', $this.dom).removeClass('plebia_active');
        $('.plebia_season_selector a.plebia_season_'+season_number, $this.dom).addClass('plebia_active');

        // Show only the selected season
        $('.plebia_season_list .plebia_season', $this.dom).hide().removeClass('plebia_active');
        $('.plebia_season_list .plebia_season_'+season_number, $this.dom).show().addClass('plebia_active');
    };


    // Season ///////////////////////////////////////////////////////////////////////////

    $.plebia.Season = function(dom, series_dom) {
        dom[0].season = this;
        this.dom = dom;
        this.series_dom = series_dom;
        this.post_dom = series_dom[0].series.post_dom;
        this.stream_dom = series_dom[0].series.stream_dom;
        this.plebia_dom = series_dom[0].series.plebia_dom;
    };

    // APIObject inheritance
    $.plebia.Season.prototype = new $.plebia.APIObject();
    $.plebia.Season.prototype.constructor = $.plebia.Season;

    $.plebia.Season.prototype.init = function(api_season_url) {
        // Populate post DOM with templates and values from API

        var $this = this;
        var deferred = $.Deferred();

        // Copy base template
        var content_template = $('.plebia_template .plebia_season_template', $this.plebia_dom).html();
        $this.dom.html(content_template);
        
        // Class name
        $this.dom.addClass('plebia_season');

        // Record API URL
        $this.api_set_url(api_season_url);

        // Load DOM content
        $.when($this.load()).done(function() {
            deferred.resolve();
        });

        return deferred.promise();
    };

    $.plebia.Season.prototype.load = function() {
        // Load episodes in template

        var $this = this;
        var deferred = $.Deferred();

        // Get season details from API
        $.when($this.api_load()).done(function() {
            // Season number
            $('.plebia_season_title .plebia_number', $this.dom).html($this.api_obj.number);
            $this.dom.addClass('plebia_season_'+$this.api_obj.number);

            // Episodes
            for(i in $this.api_obj.episode_list) {
                var api_episode_obj = $this.api_obj.episode_list[i];

                // Create episode DOM
                var episode_dom = $('<div></div>');
                $('.plebia_episode_list', $this.dom).append(episode_dom);

                // Init episode object using already retreived API object
                var episode = new $.plebia.Episode(episode_dom, $this.dom);
                episode.init(api_episode_obj);
            }

            deferred.resolve();
        });

        return deferred.promise();
    };

    $.plebia.Season.prototype.update = function() {
        var $this = this;
        var deferred = $.Deferred();

        var elems = $('.plebia_state_searching, .plebia_state_not_aired, .plebia_state_queued, .plebia_state_downloading, .plebia_state_transcoding_not_ready', $this.dom);
        var count = elems.length;

        // Refresh season if any episode needs update
        if(count>0) {
            $.when($this.api_load()).done(function() {
                for(i in $this.api_obj.episode_list) {
                    var episode_dom = $('.plebia_episode:nth('+i+')', $this.dom);
                    var episode = episode_dom[0].episode;
                    var episode_api_obj = $this.api_obj.episode_list[i];
                    
                    // Refresh individual episode
                    var dfr = episode.update(episode_api_obj);
                    
                    if(!--count) { // at the last item
                        deferred.resolve();
                    }
                }
            });
        } else {
            deferred.resolve();
        }

        return deferred.promise();
    };


    // StatefulDOM //////////////////////////////////////////////////////////////////////

    $.plebia.StatefulDOM = function() {};

    // BaseObject inheritance
    $.plebia.StatefulDOM.prototype = new $.plebia.BaseObject();
    $.plebia.StatefulDOM.prototype.constructor = $.plebia.StatefulDOM; 

    // List of states 
    $.plebia.StatefulDOM.prototype.state_list = new Array("new",
                                                          "searching",
                                                          "not_aired",
                                                          "queued",
                                                          "downloading",
                                                          "transcoding_not_ready",
                                                          "all_ready",
                                                          "error");

    $.plebia.StatefulDOM.prototype.update_dom = function() {
        // Populate DOM based on an object

        var $this = this;

        // Check if we need to change state
        var dom_state = $this.get_dom_state();
        var obj_state = $this.get_obj_state();

        if(dom_state != obj_state) {
            $this.set_dom_state(obj_state);
            $this.load_state_template(obj_state);
        }

        // Some states have custom update methods
        if('update_state_'+obj_state in $this) {
            $this['update_state_'+obj_state](dom_state);
        }
    };

    $.plebia.StatefulDOM.prototype.get_dom_state = function() {
        // Determine in which state the episode is on the DOM

        $this = this;
        for(i in $this.state_list) {
            var state = $this.state_list[i];
            if($this.dom.hasClass('plebia_state_'+state)) {
                return state;
            }
        }
        return 'no_state';
    };

    $.plebia.StatefulDOM.prototype.set_dom_state = function(new_state) {
        // Set the right state class on the episode <div> (add current one & remove other states)

        $this = this;
        for(i in $this.state_list) {
            var state = $this.state_list[i];
            if(state != new_state) {
                $this.dom.removeClass('plebia_state_'+state);
            } else {
                $this.dom.addClass('plebia_state_'+state);
            }
        }
    };

    $.plebia.StatefulDOM.prototype.get_obj_state = function() {
        // Determine in which state it is on the API

        // To subclass
    };

    $.plebia.StatefulDOM.prototype.load_state_template = function(state) {
        // Replace the content <div> by its state template
        
        // To subclass
    };


    // Episode //////////////////////////////////////////////////////////////////////////

    $.plebia.Episode = function(dom, season_dom) {
        dom[0].episode = this;
        this.dom = dom;
        this.season_dom = season_dom;
        this.series_dom = season_dom[0].season.series_dom;
        this.post_dom = season_dom[0].season.post_dom;
        this.stream_dom = season_dom[0].season.stream_dom;
        this.plebia_dom = season_dom[0].season.plebia_dom;
    };

    // APIObject inheritance
    $.plebia.Episode.prototype = new $.plebia.APIObject();
    $.plebia.Episode.prototype.constructor = $.plebia.Episode;

    // StatefulDOM inheritance
    $.plebia.extend($.plebia.Episode.prototype, $.plebia.StatefulDOM.prototype);

    $.plebia.Episode.prototype.init = function(api_episode_obj) {
        // Populate post DOM with templates and values from API

        var $this = this;

        // Copy base template
        var content_template = $('.plebia_template .plebia_episode_small_template', $this.plebia_dom).html();
        $this.dom.html(content_template);

        // API URL
        $this.api_set_url(api_episode_obj.resource_uri);
        $this.api_obj = api_episode_obj;

        // Set values in base template (everything not state related)
        $this.set_base_values();
        
        // Class name
        $this.dom.addClass('plebia_episode');

        // Populate post with actual data
        $this.update_dom(api_episode_obj);
    };

    $.plebia.Episode.prototype.set_base_values = function() {
        // Set values on DOM template which don't depend on current state

        var $this = this;

        $('.plebia_number', $this.dom).html($this.api_obj.number);
        $('.plebia_title', $this.dom).html($this.api_obj.name.substring(0,45));
        $('.plebia_overview', $this.dom).html($this.api_obj.overview.substring(0,145)+'...');

        // Bind method to click on episode
        $('a.plebia_episode_link', $this.dom).click(function() {
            var episode_dom = $(this).parents('.plebia_episode');
            var episode_obj = episode_dom[0].episode;
            episode_obj.on_click();
        });
    };

    $.plebia.Episode.prototype.update = function(api_obj) {
        // Refresh episode using provided API object

        var $this = this;

        // Update API object
        $this.api_obj = api_obj;

        // Update DOM
        $this.update_dom();
    };

    $.plebia.Episode.prototype.get_obj_state = function() {
        // Determine in which state the episode is on the API

        var $this = this;
        var yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        
        // Episodes which haven't aired yet
        if(Date.parse($this.api_obj.first_aired) > yesterday) {
            return 'not_aired';
        }

        // Video processing
        if($this.api_obj.video) {
            var video = $this.api_obj.video;

            if(video.status == 'New') {
                return 'downloading';
            } else if(video.status == 'Queued' || video.status == 'Transcoding') {
                return 'transcoding_not_ready';
            } else if(video.status == 'Completed') {
                return 'all_ready';
            } else {
                return 'error';
            }

        // Torrent processing
        } else if($this.api_obj.torrent) {
            var torrent = $this.api_obj.torrent;

            if(torrent.status == 'New' || torrent.status == 'Downloading metadata') {
                return 'searching';
            } else if(torrent.status == 'Queued') {
                return 'queued';
            } else if(torrent.status == 'Downloading' || torrent.status == 'Completed') {
                return 'downloading';
            } else {
                return 'error';
            }
        } else {
            return 'queued';
        }
    };

    $.plebia.Episode.prototype.load_state_template = function(state) {
        // Replace the content <div> of an episode by its state template

        $this = this;
        var state_template = $('.plebia_template .plebia_episode_small_states .plebia_episode_'+state, $this.plebia_dom);
        $('.plebia_state', $this.dom).html(state_template.html());
    };

    $.plebia.Episode.prototype.on_click = function() {
        // When current episode is clicked in season listing

        $this = this;
        var deferred= $.Deferred();

        // Launch watchbox
        var watchbox = $this.plebia_dom[0].watchbox;
        $.when(watchbox.show($this.dom)).done(function() {
            deferred.resolve();
        });
        
        return deferred.promise();
    };
    
    // States updates ///////////

    $.plebia.Episode.prototype.update_state_searching = function(old_state) {
        var $this = this;

        if(old_state != 'searching') {
            // Progress bar init
            $('.plebia_progress_bar', $this.dom).progressbar({value: 0});
        }
    };
    
    $.plebia.Episode.prototype.update_state_not_aired = function(old_state) {
        var $this = this;

        if(old_state != 'not_aired') {
            $('.plebia_air_date', $this.dom).html($this.api_obj.first_aired.substring(0,10));
        }
    };
    
    $.plebia.Episode.prototype.update_state_downloading = function(old_state) {
        var $this = this;

        if(old_state != 'downloading') {
            // Progress bar init
            $('.plebia_progress_bar', $this.dom).progressbar({value: 0});
        }

        // Progress % and progress bar
        var progress = Math.round($this.api_obj.torrent.progress*100);
        $('.plebia_percent .plebia_percent_value', $this.dom).html(progress);
        $('.plebia_progress_bar', $this.dom).progressbar('option', 'value', Math.round(progress));
        // ETA
        var human_eta = $.plebia.human_eta($this.api_obj.torrent.eta);
        $('.plebia_eta .plebia_eta_value', $this.dom).html(human_eta);
    };

    $.plebia.Episode.prototype.update_state_transcoding_not_ready = function(old_state) {
        var $this = this;

        if(old_state != 'transcoding_not_ready') {
            // Thumb
            $('.plebia_thumb', $this.dom).attr('src', encodeURI('/downloads/' + $this.api_obj.video.image_path));
        }
    };
    
    $.plebia.Episode.prototype.update_state_all_ready = function(old_state) {
        var $this = this;

        if(old_state != 'all_ready') {
            // Thumb
            $('.plebia_thumb', $this.dom).attr('src', encodeURI('/downloads/' + $this.api_obj.video.image_path));
        }
    };
    

    // Watchbox /////////////////////////////////////////////////////////////////////////

    $.plebia.WatchBox = function(dom, plebia_dom) {
        // Attach Watchbox object to template, but let dom attribute unset
        // fancybox clones the content when launched, and we want to alter to copy, not the template
        var $this = this;
        dom[0].watchbox = $this;
        $this.dom = null;

        $this.plebia_dom = plebia_dom;
        $this.episode_dom = null;

        // Create a copy of the template
        // (fancybox moves it to the watchbox the first time)
        var watchbox_template = $('.plebia_template .plebia_watchbox', $this.plebia_dom);
        watchbox_template.clone().attr('id', 'plebia_watchbox').appendTo(watchbox_template.parent())
    };

    // BaseObject inheritance
    $.plebia.WatchBox.prototype = new $.plebia.BaseObject();
    $.plebia.WatchBox.prototype.constructor = $.plebia.WatchBox; 

    // StatefulDOM inheritance
    $.plebia.extend($.plebia.WatchBox.prototype, $.plebia.StatefulDOM.prototype);

    $.plebia.WatchBox.prototype.show = function(episode_dom) {
        // Display the watchbox for a given episode

        var $this = this;
        var deferred= $.Deferred();

        $this.episode_dom = episode_dom;
        
        // Lightbox
        $.fancybox({
            'padding'		: 0,
            'autoDimensions': false,
            'width'		    : 1000,
            'height'		: 650,
            'href'			: '#plebia_watchbox',
            'onComplete'    : function() {
                // Now we can work on the DOM
                $this.show_ready();

                deferred.resolve();
            }
        });
        
        return deferred.promise();
    };

    $.plebia.WatchBox.prototype.show_ready = function() {
        // Called once the lightbox is ready - Update the box content to display episode details

        var $this = this;

        // Link object to cloned HTML
        var watchbox_dom = $('#fancybox-content .plebia_watchbox');
        watchbox_dom[0].watchbox = $this;
        $this.dom = watchbox_dom;

        // Make sure the contents of the watchbox are the template 
        // (lightbox only intialize it once, upon first appearance)
        var watchbox_template = $('.plebia_template .plebia_watchbox', $this.plebia_dom);
        $this.dom.html(watchbox_template.html());
        $this.set_dom_state('new');
        
        // Get objects containing details about the episode to display        
        var episode = $this.episode_dom[0].episode;
        var season = episode.season_dom[0].season;
        var series = season.series_dom[0].series;

        // Set values in DOM
        $('.plebia_series_title', $this.dom).html(series.api_obj.name);
        $('.plebia_description .plebia_title .plebia_name', $this.dom).html(episode.api_obj.name.substring(0,50));
        $('.plebia_description .plebia_title .plebia_season_nb', $this.dom).html(season.api_obj.number);
        $('.plebia_description .plebia_title .plebia_episode_nb', $this.dom).html(episode.api_obj.number);
        $('.plebia_description .plebia_overview', $this.dom).html(episode.api_obj.overview.substring(0,300));

        // Load state template
        $this.update_dom();
    };

    $.plebia.WatchBox.prototype.get_obj_state = function() {
        // Determine in which state it is on the API

        // Get it from the episode object
        return $this.episode_dom[0].episode.get_obj_state();
    };

    $.plebia.WatchBox.prototype.load_state_template = function(state) {
        // Replace the content <div> by its state template

        $this = this;
        var state_template = $('.plebia_template .plebia_watchbox_states .plebia_watchbox_'+state, $this.plebia_dom);
        $('.plebia_state', $this.dom).html(state_template.html());
    };

    $.plebia.WatchBox.prototype.get_download_url = function() {
        // Build the URL to the original video of a given post, if possible
        $this = this;
        var episode = $this.episode_dom[0].episode;
        var video = episode.api_obj.video;

        var url = encodeURI('/downloads/' + video.original_path);
        return url;
    };

    // XXX TODO
    $.plebia.WatchBox.prototype.set_next = function() {
        // Add the callback to add the next episode when the link is clicked
        $this = this;
        var deferred= $.Deferred();
        var next_episode_dom = $('.plebia_next_episode', post_dom);

        $.when($this.get_api_object('series', post_dom)).done(function(series) {
            $.when($this.get_api_object('episode', post_dom)).done(function(episode) {
                $.when($this.get_api_object_by_id(episode.next_episode)).done(function(next_episode) {
                    $.when($this.get_api_object_by_id(next_episode.season)).done(function(next_episode_season) {

                        // Set values of next episode
                        $('.plebia_name', next_episode_dom).val(series.name);
                        $('.plebia_season_nb', next_episode_dom).val(next_episode_season.number);
                        $('.plebia_episode_nb', next_episode_dom).val(next_episode.number);

                        // Form submit
                        $('a', next_episode_dom).click(function(){
                            $(this).parent().submit();
                            return false;
                        });

                        deferred.resolve();
                    });
                // Last episode
                }).fail(function() {
                    $('a', next_episode_dom).remove();
                    $('form', next_episode_dom).prepend('<p>(Last episode)</p>')
                });
            });
        });

        return deferred.promise();
    };

    // States ///////////////////////////////////////////////////

    // STATE: searching //////////////////////
    $.plebia.WatchBox.prototype.update_state_searching = function(old_state) {
        var $this = this;

        // Check if we are entering this state now
        if(old_state != 'searching') {
            $this.load_state_template('searching');
        }
    };

    // STATE: not aired /////////////////////
    $.plebia.WatchBox.prototype.update_state_not_aired = function(old_state) {
        var $this = this;

        if(old_state != 'not_aired') {
            $this.load_state_template('not_aired');
            $('.plebia_air_date', $this.dom).html($this.api_obj.first_aired);
        }
    };
    
    // STATE: queued ////////////////////////
    $.plebia.WatchBox.prototype.update_state_queued = function(old_state) {
        var $this = this;

        // Check if we are entering this state now
        if(old_state != 'queued') {
            $this.load_state_template('queued');
        }
    };

    // STATE: downloading ////////////////////
    $.plebia.WatchBox.prototype.update_state_downloading = function(old_state) {
        var $this = this;
        var episode = $this.episode_dom[0].episode;
        var torrent = episode.api_obj.torrent;

        // Check if we are entering this state now
        if(old_state != 'downloading') {
            $this.load_state_template('downloading');

            // Click on "More" to show download details
            $('.plebia_more', $this.dom).toggle(
                function() {
                    $('.plebia_download_details', $this.dom).show('drop', { direction: "up" }, 200);
                    $('.plebia_more', $this.dom).html('Less details...');
                },
                function() {
                    $('.plebia_download_details', $this.dom).hide('drop', { direction: "up" }, 200);
                    $('.plebia_more', $this.dom).html('More details...');
                }                    
            );

            // Progress bar init
            $('.plebia_progress_bar', $this.dom).progressbar({value: 0});
        }

        // Info message
        if(torrent.progress < 1.0) {
            $('.plebia_info_msg', $this.dom).html('Video found! Starting download...');
        } else if(torrent.progress < 99.0) {
            $('.plebia_info_msg', $this.dom).html('Downloading...');
        } else {
            $('.plebia_info_msg', $this.dom).html('Finishing download...');
        }

        // Progress % and progress bar
        var progress = Math.round(torrent.progress*100)/100;
        $('.plebia_info_progress .plebia_percent', $this.dom).html(progress);
        $('.plebia_info_progress .plebia_eta', $this.dom).html(torrent.eta);
        $('.plebia_progress_bar', $this.dom).progressbar('option', 'value', Math.round(progress));
        // Do not show progress initially
        if(torrent.progress > 1.0) {
            $('.plebia_progress_bar', $this.dom).css('display', 'block');
            $('.plebia_info_progress', $this.dom).css('display', 'inline');
        } else {
            $('.plebia_progress_bar', $this.dom).css('display', 'none');
            $('.plebia_info_progress', $this.dom).css('display', 'none');
        }

        // Download details
        var dl_details = $('.plebia_download_details', $this.dom);
        $('.plebia_torrent_name .plebia_value', dl_details).html(torrent.name);
        $('.plebia_torrent_type .plebia_value', dl_details).html(torrent.type);
        $('.plebia_torrent_seeds .plebia_value', dl_details).html(torrent.seeds);
        $('.plebia_torrent_peers .plebia_value', dl_details).html(torrent.peers);
        $('.plebia_torrent_download_speed .plebia_value', dl_details).html(torrent.download_speed);
        $('.plebia_torrent_upload_speed .plebia_value', dl_details).html(torrent.upload_speed);
    };

    // STATE: transcoding_not_ready //////////
    $.plebia.WatchBox.prototype.update_state_transcoding_not_ready = function(old_state) {
        var $this = this;

        // Check if we are entering this state now
        if(old_state != 'transcoding_not_ready') {
            $this.load_state_template('transcoding_not_ready');

            // Thumb
            var episode = $this.episode_dom[0].episode;
            var video_obj = episode.api_obj.video;
            $('.plebia_thumb', $this.dom).attr('src', encodeURI('/downloads/' + video_obj.image_path));

            // Download link
            var url = $this.get_download_url();
            $('.plebia_download .video_link', $this.dom).attr('href', url);
        }
    };

    // STATE: all_ready //////////////////////
    $.plebia.WatchBox.prototype.update_state_all_ready = function(old_state) {
        var $this = this;

        // Check if we are entering this state now
        if(old_state != 'all_ready') {
            $this.load_state_template('all_ready');

            var episode = $this.episode_dom[0].episode;
            var video_obj = episode.api_obj.video;
            var video_dom = $('video', $this.dom);
            var video_src = encodeURI('/downloads/' + video_obj.webm_path);

            $('video', $this.dom).attr('poster', '/downloads/' + video_obj.image_path);
            $('source', $this.dom).attr('src', video_src);
            $('.vjs-no-video a', $this.dom).attr('href', encodeURI('/downloads/' + video_obj.webm_path));

            // video.js
            video_dom.VideoJS({
                controlsBelow: false, // Display control bar below video instead of in front of
                controlsHiding: true, // Hide controls when mouse is not over the video
                defaultVolume: 0.85, // Will be overridden by user's last volume if available
                flashVersion: 9, // Required flash version for fallback
                linksHiding: true // Hide download links when video is supported
            });
            
            // Download link
            var url = $this.get_download_url();
            $('.video_link', $this.dom).attr('href', url);
        }
    };

    // STATE: error //////////////////////////
    $.plebia.WatchBox.prototype.update_state_error = function(old_state) {
        var $this = this;

        // Check if we are entering this state now
        if(old_state != 'error') {
            $this.load_state_template('error');
        }
    };


})(jQuery);



