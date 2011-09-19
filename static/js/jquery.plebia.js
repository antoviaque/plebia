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

    $.fn.plebia_post_to_stream = function(series_id) {
        var root = this;
        var stream = $('.plebia_stream', root);

        $.plebia.post_to_stream(series_id, stream, root);
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

    $.plebia.APIObject.prototype.api_init = function(api_url) {
        // Sets URL in DOM (for debugging) and load the object attributes from the REST API URL
        
        var $this = this;

        // Record URL on DOM
        $this.api_set_url(api_url);
    };

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

    $.plebia.APIObject.prototype.api_load = function(obj_class, post_dom) {
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

        // Attach object to API URL and load attributes
        $this.api_init($this.api_base_url+'/post/?limit=50');

        // Populate stream (all posts)
        $.when($this.add_new_posts()).done(function() {
            // Init completed
            deferred.resolve();

            // Start regular update
            //$this.update_loop();
        });

        return deferred.promise();
    };

    $.plebia.Stream.prototype.add_new_posts = function(loaded_post_list) {
        // Add posts in API but not in DOM 

        var $this = this;
        var deferred = $.Deferred();

        // loaded_post_list is optional - if not provided, load all posts
        if(!loaded_post_list) {
            var loaded_post_list = new Array();
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
                $this.add_post(post_obj)
                
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

    $.plebia.Stream.prototype.update_loop = function() {
        var $this = this;

        $this.update().done(function() {
            $this.setTimeout(function() {
                $this.update_loop();
            }, 2000);
        });
    };

    // XXX To check
    $.plebia.Stream.prototype.update = function() {
        var $this = this;
        var deferred = $.Deferred();

        var loaded_post_list = new Array();
        var elems = $('.plebia_post', stream);
        var count = elems.length;

        // Load posts if there is no post yet
        if(count==0) {
            $this.load_new_posts(loaded_post_list, stream, root).done(function() {
                deferred.resolve();
            });
        }

        // Look through posts that are already loaded
        elems.each(function() {
            var post_dom = $(this);
            var post_id = $this.get_object_id_from_dom('post', post_dom);
            
            // Keep track of loaded posts ids to not reload them later on
            loaded_post_list.push(post_id);

            // Refresh individual post when marked
            // XXX extract to another method to only refresh episodes lists currently opened
            if(post_dom.hasClass('plebia_post_update')) {
                var dfr1 = $this.update_post(post_dom, stream, root);
            } else {
                var dfr1 = null;
            }

            if(!--count) { // at the last item
                var dfr2 = $this.load_new_posts(loaded_post_list, stream, root);
                
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
        $this.update(api_post_obj);
    };

    $.plebia.Post.prototype.update = function(api_post_obj) {
        // Set the HTML values in the base template
        
        var $this = this;

        // Store API values without reloading them from API
        $this.api_obj = api_post_obj;
        $this.api_set_url(api_post_obj.resource_url);

        // Update DOM
        $('.plebia_post_time', $this.dom).html(api_post_obj.date_added);
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

        // Populate post with actual data
        $this.update(api_series_obj);

        // JS for opening/closing the episodes list
        $("a.plebia_trigger", $this.dom).click(function(){
            $(".plebia_season_list", new_post).toggle("fast");
            $(this).toggleClass("plebia_active");
            
            if($(this).hasClass("plebia_active")) {
                $this.load_season_list(new_post, stream, root);
            };

            return false;
        });
    };

    $.plebia.Series.prototype.update = function(api_series_obj) {
        // Set the HTML values in the base template

        var $this = this;

        $('.plebia_poster', $this.dom).attr('src', 
                '/static/banner.php?file_path='+api_series_obj.poster_url);
        $('.plebia_name', $this.dom).html(api_series_obj.name);
        $('.plebia_overview', $this.dom).html(api_series_obj.overview);
    };

    $.plebia.Series.prototype.load_season_list = function(post_dom, stream, root) {
        // Get episodes list from API and display them in episodes list menu

        
        $.when($this.get_api_object('series', post_dom)).done(function(post) {

        });
    };

    
    
    ///////////////////////////////////////////////////////////////////////////////

    /*
    $.plebia.Updatable = function() {};
    $.plebia.Updatable.prototype.update = function() {
        this.dom.html(this.name);
    }

    $.plebia.Stream = function(stream_dom, root_dom) {
        stream_dom[0].stream = this;
        this.dom = stream_dom;
        this.root_dom = root_dom;
        this.name = "toto";
    }
    $.plebia.Stream.prototype = new $.plebia_test.Updatable();
    $.plebia.Stream.prototype.update2 = function() {
        this.dom.html(this.dom.html()+'..'+this.name);
    }
    */


    $.plebia_old = {
        post_state_list: new Array("new",
                                   "searching",
                                   "downloading",
                                   "transcoding_not_ready",
                                   "transcoding_ready",
                                   "all_ready",
                                   "error"),

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

        // Page refresh /////////////////////////////////////////////


        post_to_stream: function(series_id, stream, root) {
            var $this = this;

            // Create new post with series, add to stream
            $.getJSON('/ajax/newpost/'+series_id+'/', function(response) {
                var post_id = response[0];

                $this.load_post(post_id, stream, root, 'top');
            });
        },


        // Posts ////////////////////////////////////////////////////


        // Watchbox /////////////////////////////////////////////////

        load_watchbox: function(post_id, stream, root, position) {
            var $this = this;
            var deferred= $.Deferred();

            // Copy base template
            var new_post = $this.new_base_template(stream, root, position);

            $.Deferred(function(sub_deferred) {
                sub_deferred
                // Get related API object ids
                .pipe(function() { return $this.update_all_post_api_id(post_id, new_post); })
                // Set base template HTML
                .pipe(function() { return $this.set_post_container_values(new_post); })
                // Populate post with actual data
                .pipe(function() { return $this.update_post(new_post, stream, root); })
                .pipe(function() { deferred.resolve(); });
            }).resolve();

            return deferred.promise();
        },

        update_all_watchbox_api_id: function(post_id, post_dom) {
            // Update the API objects ids stored in the watchbox <div><input>

            var $this = this;
            var deferred= $.Deferred();

            // post id is the root id that allows to retreive all others
            $this.set_object_id_in_dom('post', post_id, post_dom);

            $.Deferred(function(sub_deferred) {
                sub_deferred
                .pipe(function() { return $this.update_api_id('post', 'episode', post_dom); })
                .pipe(function() { return $this.update_api_id('episode', 'season', post_dom); })
                .pipe(function() { return $this.update_api_id('season', 'series', post_dom); })
                .pipe(function() { return $this.update_api_id('episode', 'torrent', post_dom); })
                .pipe(function() { return $this.update_api_id('episode', 'video', post_dom); })
                .pipe(function() { deferred.resolve(); });
            }).resolve();

            return deferred.promise();
        },

        set_watchbox_container_values: function(post_dom) {
            // Set the HTML values in the base template (part common to all states)
            $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object('post', post_dom)).done(function(post) {
                // Date
                $('.plebia_post_time', post_dom).html(post.date_added);

                // Title & download link
                dfr1 = $this.get_post_title(post_dom).done(function(title) {
                    $('.plebia_post_title', post_dom).html(title);
                });
                
                // Next episode callback
                dfr2 = $this.set_next_episode(post_dom);

                // Wait until both have completed
                $.when(dfr1, dfr2).then(function() {
                    deferred.resolve();
                });
            });
            
            return deferred.promise();
        },

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

        update_watchbox: function(post_dom, stream, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we need to change state
            var dom_state = $this.get_post_state_from_dom(post_dom);
            $this.get_post_state_from_api(post_dom).done(function(obj_state) {
                if(dom_state != obj_state) {
                    $this.set_post_state_in_dom(obj_state, post_dom);
                }

                // There is a different update method for each state
                $this['update_post_'+obj_state](dom_state, post_dom, root).done(function() {
                    deferred.resolve();
                });
            });

            return deferred.promise();
        },

        get_watchbox_state_from_dom: function(post_dom) {
            // Determine in which state the post is on the DOM

            $this = this;
            for(i in $this.post_state_list) {
                var state = $this.post_state_list[i];
                if(post_dom.hasClass('plebia_post_'+state)) {
                    return state;
                }
            }
            return 'no_state';
        },

        set_watchbox_state_in_dom: function(obj_state, post_dom) {
            // Set the right state class on the post <div> (add current one & remove other states)

            $this = this;
            for(i in $this.post_state_list) {
                var state = $this.post_state_list[i];
                if(state != obj_state) {
                    post_dom.removeClass('plebia_post_'+state);
                } else {
                    post_dom.addClass('plebia_post_'+state);
                }
            }
        },

        get_watchbox_state_from_api: function(post_dom) {
            // Determine in which state the post is on the API

            $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object('episode', post_dom)).done(function(episode) {
                // Video processing
                if(episode.video) {
                    $this.set_object_id_in_dom('video', episode.video, post_dom);
                    $.when($this.get_api_object('video', post_dom)).done(function(video) {
                        if(video.status == 'New') {
                            deferred.resolve('downloading');
                        } else if(video.status == 'Transcoding') {
                            deferred.resolve('transcoding_not_ready');
                        } else if(video.status == 'Completed') {
                            deferred.resolve('all_ready');
                        } else {
                            deferred.resolve('error');
                        }
                    });
                // Torrent processing
                } else if(episode.torrent) {
                    $this.set_object_id_in_dom('torrent', episode.torrent, post_dom);
                    $.when($this.get_api_object('torrent', post_dom)).done(function(torrent) {
                        if(torrent.status == 'New') {
                            deferred.resolve('searching');
                        } else if(torrent.status=='Downloading' || torrent.status=='Completed') {
                            deferred.resolve('downloading');
                        } else {
                            deferred.resolve('error');
                        }
                    });
                } else {
                    deferred.resolve('error');
                }
            });

            return deferred.promise();
        },

        set_watchbox_content_from_template: function(obj_state, post_dom, root) {
            // Replace the content <div> of a post by its state template

            $this = this;
            var state_template = $('.plebia_post_content_states .plebia_post_'+obj_state, root);
            $('.plebia_post_content', post_dom).html(state_template.html());
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


        // API interaction //////////////////////////////////////////



    };

    $(window).bind("beforeunload", function() {
        $.plebia.error = $.plebia.noop;
    });

})(jQuery);



