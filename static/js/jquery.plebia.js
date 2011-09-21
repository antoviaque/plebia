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
        // Display the stream
        var stream_dom = $('.plebia_stream', this.dom);
        var stream = new $.plebia.Stream(stream_dom, this.dom);
        stream.init();

        // Dress buttons
        $('input:submit', this.dom).button();

        // Load auto-suggest
        $('.plebia_header input.plebia_name', this.dom).liveSearch({url: '/ajax/search/'});

        // Add feedback tab
        var uv = document.createElement('script'); uv.type = 'text/javascript'; uv.async = true;
        uv.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'widget.uservoice.com/6PhXO6580egdGy3eefwsAg.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(uv, s);
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
        $this.api_set_url($this.api_base_url+'/post/?limit=50');

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

        // Create new post on server with series, add to stream
        $.getJSON('/ajax/newpost/'+series_id+'/', function(response) {
            $this.update();
        });
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
        // Reload content if necessary

        // XXX TODO
        /*if(post_dom.hasClass('plebia_post_update')) {
            var dfr1 = $this.update_post(post_dom, stream, root);
        } else {
            var dfr1 = null;
        }*/
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
            $(".plebia_season_list", $this.dom).toggle("fast");
            $(this).toggleClass("plebia_active");
            
            if($(this).hasClass("plebia_active")) {
                $this.load_season_list();
            } else {
                $('.plebia_season_list', $this.dom).html('');
            }

            return false;
        });
    };

    $.plebia.Series.prototype.load = function(api_series_obj) {
        // Set the HTML values in the base template

        var $this = this;

        $('.plebia_poster', $this.dom).attr('src', '/static/banner.php?file_path='+$this.api_obj.poster_url);
        $('.plebia_name', $this.dom).html($this.api_obj.name);
        $('.plebia_overview', $this.dom).html($this.api_obj.overview.substring(0,320));
    };

    $.plebia.Series.prototype.load_season_list = function() {
        // Get episodes list from API and display them in episodes list menu

        var $this = this;
        var season_list_dom = $('.plebia_season_list', $this.dom);
        
        // Load all seasons
        for(i in $this.api_obj.season_list) {
            var api_season_url = $this.api_obj.season_list[i];

            // Create season DOM
            var season_dom = $('<div></div>');
            $('.plebia_season_list', $this.dom).append(season_dom);

            // Init season object, which populates the DOM using API call
            var season = new $.plebia.Season(season_dom, $this.dom);
            season.init(api_season_url);
        }
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

        // Copy base template
        var content_template = $('.plebia_template .plebia_season_template', $this.plebia_dom).html();
        $this.dom.html(content_template);
        
        // Class name
        $this.dom.addClass('plebia_season');

        // Record API URL
        $this.api_set_url(api_season_url);

        // Load DOM content
        $this.load();
    };

    $.plebia.Season.prototype.load = function() {
        // Load episodes in template

        var $this = this;

        // Get season details from API
        $.when($this.api_load()).done(function() {
            // Season number
            $('.plebia_season_title .plebia_number', $this.dom).html($this.api_obj.number);

            // Episodes
            for(i in $this.api_obj.episode_list) {
                var api_episode_obj = $this.api_obj.episode_list[i];

                // Create episode DOM
                var episode_dom = $('<div></div>');
                $this.dom.append(episode_dom);

                // Init episode object using already retreived API object
                var episode = new $.plebia.Episode(episode_dom, $this.dom);
                episode.init(api_episode_obj);
            }
        });
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

    // List of states 
    $.plebia.Episode.prototype.state_list = new Array("new",
                                                      "not_started",
                                                      "searching",
                                                      "downloading",
                                                      "transcoding_not_ready",
                                                      "all_ready",
                                                      "error");

    $.plebia.Episode.prototype.init = function(api_episode_obj) {
        // Populate post DOM with templates and values from API

        var $this = this;

        // API URL
        $this.api_set_url(api_episode_obj.resource_uri);
        $this.api_obj = api_episode_obj;

        // Copy base template & set values
        var content_template = $('.plebia_template .plebia_episode_small_template', $this.plebia_dom).html();
        $this.dom.html(content_template);
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
    };

    $.plebia.Episode.prototype.update = function() {
        // Refresh episode from API

        var $this = this;
        var deferred= $.Deferred();

        // Update API object
        $.when($this.api_load()).done(function() {
            // Update DOM
            $.when($this.update_dom()).done(function() {
                deferred.resolve();
            });
        });
    };

    $.plebia.Episode.prototype.update_dom = function() {
        // Populate episode DOM based on API (uses stored object, doesn't fetch from API)

        var $this = this;
        var deferred= $.Deferred();

        // Check if we need to change state
        var dom_state = $this.get_dom_state();
        var obj_state = $this.get_api_state();

        if(dom_state != obj_state) {
            $this.set_dom_state(obj_state);
            $this.load_state_template(obj_state);
        }

        // There is a different update method for each state
        //$this['update_'+obj_state](dom_state).done(function() {
            deferred.resolve();
        //});

        return deferred.promise();
    };

    $.plebia.Episode.prototype.get_dom_state = function() {
        // Determine in which state the episode is on the DOM

        $this = this;
        for(i in $this.state_list) {
            var state = $this.state_list[i];
            if($this.dom.hasClass('plebia_episode_'+state)) {
                return state;
            }
        }
        return 'no_state';
    };

    $.plebia.Episode.prototype.set_dom_state = function(new_state) {
        // Set the right state class on the episode <div> (add current one & remove other states)

        $this = this;
        for(i in $this.state_list) {
            var state = $this.state_list[i];
            if(state != new_state) {
                $this.dom.removeClass('plebia_episode_'+state);
            } else {
                $this.dom.addClass('plebia_episode_'+state);
            }
        }
    };

    $.plebia.Episode.prototype.get_api_state = function() {
        // Determine in which state the episode is on the API

        $this = this;

        // Video processing
        if($this.api_obj.video) {
            var video = $this.api_obj.video;

            if(video.status == 'New') {
                return 'downloading';
            } else if(video.status == 'Transcoding') {
                return 'transcoding_not_ready';
            } else if(video.status == 'Completed') {
                return 'all_ready';
            } else {
                return 'error';
            }

        // Torrent processing
        } else if($this.api_obj.torrent) {
            var torrent = $this.api_obj.torrent;

            if(torrent.status == 'New') {
                return 'searching';
            } else if(torrent.status=='Downloading' || torrent.status=='Completed') {
                return 'downloading';
            } else {
                return 'error';
            }
        } else {
            return 'not_started';
        }
    };

    $.plebia.Episode.prototype.load_state_template = function(state) {
        // Replace the content <div> of an episode by its state template

        $this = this;
        var state_template = $('.plebia_template .plebia_episode_small_states .plebia_episode_'+state, $this.plebia_dom);
        $('.plebia_state', $this.dom).html(state_template.html());
    };

    
    
    ///////////////////////////////////////////////////////////////////////////////


    $.plebia_old = {

        // TEMP ////////////////////////////////////////////////////

        click_on_episode_list: function(){
            var element = $(".plebia .plebia_stream .plebia_post .plebia_episode_list");



            // Progress bar
            $('.plebia_progress_bar', element).progressbar({value: 14});
            $('.plebia_progress_bar_new', element).progressbar({value: 0});

            // Lightbox
            $(".plebia_episode_link").click(function() {
                $.fancybox({
                        'padding'		: 0,
                        'autoDimensions': false,
                        'width'		    : 1000,
                        'height'		: 650,
                        'href'			: '#plebia_episode_lightbox',
                    });

                return false;
            });
        },


        // Watchbox /////////////////////////////////////////////////

        get_watchbox_title: function(post_dom) {
            // Build the title for this post (including download link if applicable)
            $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object('episode', post_dom)).done(function(episode) {
                $.when($this.get_api_object('season', post_dom)).done(function(season) {
                    $.when($this.get_api_object('series', post_dom)).done(function(series) {
                        var title = series.name+' - Season '+season.number+', Episode '+episode.number;
                        $this.get_download_url(post_dom).done(function(url) {
                            title += '&nbsp;&nbsp;<img src="/static/img/download.png" class="plebia_download_icon" />';
                            var link = '<a href="'+url+'">'+title+'</a>';
                            deferred.resolve(link);
                        }).fail(function() {
                            deferred.resolve(title);
                        });
                    });
                });
            });
            
            return deferred.promise();
        },

        get_download_url: function(post_dom) {
            // Build the URL to the original video of a given post, if possible
            $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object('video', post_dom)).done(function(video) {
                if(video.status == 'Transcoding' || video.status == 'Completed') {
                    var url = '/downloads/' + video.original_path;
                    deferred.resolve(url);
                } else {
                    deferred.reject();
                }
            }).fail(function() {
                deferred.reject();
            });

            return deferred.promise();
        },

        // XXX Watchbox
        set_next_episode: function(post_dom) {
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
        },


        // States ///////////////////////////////////////////////////

        // STATE: searching //////////////////////
        update_state_searching: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'searching') {
                $this.set_post_content_from_template('searching', post_dom, root);
            }

            deferred.resolve();

            return deferred.promise();
        },

        // STATE: downloading ////////////////////
        update_state_downloading: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'downloading') {
                $this.set_post_content_from_template('downloading', post_dom, root);

                // Click on "More" to show download details
                $('.plebia_more', post_dom).toggle(
                    function() {
                        $('.plebia_download_details', post_dom).show('drop', { direction: "up" }, 200);
                        $('.plebia_more', post_dom).html('Less details...');
                    },
                    function() {
                        $('.plebia_download_details', post_dom).hide('drop', { direction: "up" }, 200);
                        $('.plebia_more', post_dom).html('More details...');
                    }                    
                );

                // Progress bar init
                $('.plebia_progress_bar', post_dom).progressbar({value: 0});
            }

            $.when($this.get_api_object('torrent', post_dom)).done(function(torrent) {
                // Info message
                if(torrent.progress < 1.0) {
                    $('.plebia_info_msg', post_dom).html('Video found! Starting download...');
                } else if(torrent.progress < 99.0) {
                    $('.plebia_info_msg', post_dom).html('Downloading...');
                } else {
                    $('.plebia_info_msg', post_dom).html('Finishing download...');
                }

                // Progress % and progress bar
                var progress = Math.round(torrent.progress*100)/100;
                $('.plebia_info_progress .plebia_percent', post_dom).html(progress);
                $('.plebia_info_progress .plebia_eta', post_dom).html(torrent.eta);
                $('.plebia_progress_bar', post_dom).progressbar('option', 'value', Math.round(progress));
                // Do not show progress initially
                if(torrent.progress > 1.0) {
                    $('.plebia_progress_bar', post_dom).css('display', 'block');
                    $('.plebia_info_progress', post_dom).css('display', 'inline');
                } else {
                    $('.plebia_progress_bar', post_dom).css('display', 'none');
                    $('.plebia_info_progress', post_dom).css('display', 'none');
                }

                // Download details
                var dl_details = $('.plebia_download_details', post_dom);
                $('.plebia_torrent_name .plebia_value', dl_details).html(torrent.name);
                $('.plebia_torrent_type .plebia_value', dl_details).html(torrent.type);
                $('.plebia_torrent_seeds .plebia_value', dl_details).html(torrent.seeds);
                $('.plebia_torrent_peers .plebia_value', dl_details).html(torrent.peers);
                $('.plebia_torrent_download_speed .plebia_value', dl_details).html(torrent.download_speed);
                $('.plebia_torrent_upload_speed .plebia_value', dl_details).html(torrent.upload_speed);

                deferred.resolve();
            });

            return deferred.promise();
        },

        // STATE: transcoding_not_ready //////////
        update_state_transcoding_not_ready: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'transcoding_not_ready') {
                $this.set_post_content_from_template('transcoding_not_ready', post_dom, root);

                // Download link on title
                $this.get_post_title(post_dom).done(function(title) {
                    $('.plebia_post_title', post_dom).html(title);

                    $this.get_download_url(post_dom).then(function(url) {
                        $('.plebia_download .video_link', post_dom).attr('href', url);

                        deferred.resolve();
                    });
                });
            }

            return deferred.promise();
        },

        // STATE: all_ready //////////////////////
        update_state_all_ready: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'all_ready') {
                $this.set_post_content_from_template('all_ready', post_dom, root);

                // Don't update this post anymore
                post_dom.removeClass('plebia_post_update');

                // Video init
                var dfr1 = $this.get_api_object('video', post_dom);
                $.when(dfr1).done(function(video) {
                    $this.init_video(video, post_dom, false);
                });

                // Download link on title
                var dfr2 = $this.get_post_title(post_dom).done(function(title) {
                    $('.plebia_post_title', post_dom).html(title);
                });

                $.when(dfr1, dfr2).done(function() {
                    deferred.resolve();
                });
            }

            return deferred.promise();
        },

        init_video: function(video_obj, post_dom, streaming) {
            var video_dom = $('video', post_dom);

            // URLs
            if(streaming) {
                var video_src = '/static/stream.php?file_path=' + video_obj.webm_path;
            } else {
                var video_src = '/downloads/' + video_obj.webm_path;
            }
            $('video', post_dom).attr('poster', '/downloads/' + video_obj.image_path);
            $('source', post_dom).attr('src', video_src);
            $('.vjs-no-video a', post_dom).attr('href', '/downloads/' + video_obj.webm_path);

            // video.js
            video_dom.VideoJS({
                controlsBelow: false, // Display control bar below video instead of in front of
                controlsHiding: true, // Hide controls when mouse is not over the video
                defaultVolume: 0.85, // Will be overridden by user's last volume if available
                flashVersion: 9, // Required flash version for fallback
                linksHiding: true // Hide download links when video is supported
            });
        },

        // STATE: error //////////////////////////
        update_state_error: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'error') {
                $this.set_post_content_from_template('error', post_dom, root);
                
                // Don't update this post anymore
                post_dom.removeClass('plebia_post_update');
            }

            deferred.resolve();

            return deferred.promise();
        },


    };

    $(window).bind("beforeunload", function() {
        $.plebia.error = $.plebia.noop;
    });

})(jQuery);



