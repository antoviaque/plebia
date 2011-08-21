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

        var root = this;
        var stream = $('.plebia_stream', root);
        
        // Dress buttons
        $('input:submit').button();

        // Display the stream
        $.plebia.bootstrap_stream(stream, root);

        // Load auto-suggest
        $("#id_name").suggest({type:'/tv/tv_program'});

        // Add feedback tab
        var uv = document.createElement('script'); uv.type = 'text/javascript'; uv.async = true;
        uv.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'widget.uservoice.com/6PhXO6580egdGy3eefwsAg.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(uv, s);
    };

    $.plebia = {
        url: "/api/v1",

        cache: {},

        window: window,

        location: location,

        noop: function() {},

        error: function(error) { alert(error); },

        setTimeout: function(cb, delay) { return $.plebia.window.setTimeout(cb, delay); },

        setInterval: function(cb, delay) { return $.plebia.window.setInterval(cb, delay); },

        post_state_list: new Array("new",
                                   "searching",
                                   "downloading",
                                   "transcoding_not_ready",
                                   "transcoding_ready",
                                   "all_ready",
                                   "error"),

        ajax: function(o) {
            return jQuery.ajax(o);
        },

        bootstrap_stream: function(stream, root) {
            this.refresh_stream(stream, root);
        },

        refresh_stream: function(stream, root) {
            var $this = this;
            var loaded_post_list = new Array();
            var deferred = $.Deferred();

            // Empty the cache
            $this.cache = {};

            // Do this every X seconds
            deferred.done(function() {
                $this.setTimeout(function() {
                    $this.refresh_stream(stream, root);
                }, 2000);
            });

            // Iter over the existing posts
            var elems = $('.plebia_post', stream);
            var count = elems.length;

            // Make sure posts are loaded even if there is no post
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
        },

        load_new_posts: function(loaded_post_list, stream, root) {
            var $this = this;
            var deferred = $.Deferred();

            // Get latest posts from API
            $.getJSON($this.url+'/post/?limit=50', function(post_list) {
                var new_post_list = new Array();

                // Identify all posts that haven't been loaded yet
                for(i in post_list.objects) {
                    var post_obj = post_list.objects[i];
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
                    $this.load_post(post_obj.resource_uri, stream, root).done(function() {
                        // When the last post has finished loading, we're done
                        if(count == 0) {
                            deferred.resolve();
                        };
                    });
                });
            });

            return deferred.promise();
        },

        load_post: function(post_id, stream, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Copy base template
            var new_post = $this.new_base_template(stream, root);

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

        new_base_template: function(stream, root) {
            // Copy base template
            var new_post = $('.plebia_post_templates .plebia_post', root).clone();
            stream.append(new_post);
            
            return new_post;
        },

        update_all_post_api_id: function(post_id, post_dom) {
            // Update the API objects ids stored in the post <div><input>

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

        set_post_container_values: function(post_dom) {
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

        get_post_title: function(post_dom) {
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

        set_next_episode: function(post_dom) {
            // Add the callback to add the next episode when the link is clicked
            $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object('episode', post_dom)).done(function(episode) {
                $.when($this.get_api_object('season', post_dom)).done(function(season) {
                    $.when($this.get_api_object('series', post_dom)).done(function(series) {
                        next_episode_dom = $('.plebia_next_episode', post_dom);

                        // Set values of next episode
                        $('.plebia_name', next_episode_dom).val(series.name);
                        $('.plebia_season_nb', next_episode_dom).val(season.number);
                        $('.plebia_episode_nb', next_episode_dom).val(episode.number+1);

                        // Form submit
                        $('a', next_episode_dom).click(function(){
                            $(this).parent().submit();
                            return false;
                        });

                        deferred.resolve();
                    });
                });
            });

            return deferred.promise();
        },

        update_api_id: function(parent_obj_class, obj_class, post_dom) {
            // Retreive the parent object from the API to update the object id on the DOM
            var $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object(parent_obj_class, post_dom))
            .done(function(parent_obj) {
                $this.set_object_id_in_dom(obj_class, parent_obj[obj_class], post_dom);
                deferred.resolve();
            })
            .fail(function() {
                $this.set_object_id_in_dom(obj_class, '', post_dom);
                deferred.resolve();
            });

            return deferred.promise();
        },

        get_api_object: function(obj_class, post_dom) {
            // Get the id stored on the post DOM and return corresponding object from API

            var $this = this;

            var obj_id = $this.get_object_id_from_dom(obj_class, post_dom);
            var deferred = $this.get_api_object_by_id(obj_id);

            return deferred;
        },

        get_object_id_from_dom: function(obj_class, post_dom) {
            // Get the id stored on the post DOM for a given class

            var $this = this;
            
            var input_name = '.plebia_'+obj_class+'_api_id';
            var obj_id = $(input_name, post_dom).val();

            return obj_id;
        },

        set_object_id_in_dom: function(obj_class, obj_id, post_dom) {
            // Set the id stored on the post DOM for a given class

            var $this = this;
            
            var input_name = '.plebia_'+obj_class+'_api_id';
            var obj_id = $(input_name, post_dom).val(obj_id);

            return obj_id;
        },

        get_api_object_by_id: function(obj_id){
            // Get an object from the API using its id (uses cached if available)
            
            var $this = this;

            // Check if it is in cache
            var cached_obj = $this.cache[obj_id];
            if(cached_obj) {
                return cached_obj;
            } else {
                // Otherwise return a deferred, to be able to handle both cases identically
                var deferred = $.getJSON(obj_id);
                deferred.done(function(obj) {
                    $this.cache[obj_id] = obj;
                });
                return deferred;
            };
        },

        update_post: function(post_dom, stream, root) {
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

        get_post_state_from_dom: function(post_dom) {
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

        set_post_state_in_dom: function(obj_state, post_dom) {
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

        get_post_state_from_api: function(post_dom) {
            // Determine in which state the post is on the API

            $this = this;
            var deferred= $.Deferred();

            $.when($this.get_api_object('episode', post_dom)).done(function(episode) {
                // Video processing
                if(episode.video) {
                    $this.set_object_id_in_dom('video', episode.video, post_dom);
                    $.when($this.get_api_object('video', post_dom)).done(function(video) {
                        if(video.status == 'Error') {
                            deferred.resolve('error');
                        } else if(video.status == 'Completed') {
                            deferred.resolve('all_ready');
                        //} else if(video.status == 'Transcoding') {
                        //    deferred.resolve('transcoding_ready');
                        } else {
                            deferred.resolve('transcoding_not_ready');
                        }
                    });
                // Torrent processing
                } else if(episode.torrent) {
                    $this.set_object_id_in_dom('torrent', episode.torrent, post_dom);
                    $.when($this.get_api_object('torrent', post_dom)).done(function(torrent) {
                        if(torrent.status == 'Error') {
                            deferred.resolve('error');
                        } else if(torrent.status == 'New') {
                            deferred.resolve('searching');
                        } else {
                            deferred.resolve('downloading');
                        }
                    });
                } else {
                    deferred.resolve('error');
                }
            });

            return deferred.promise();
        },

        set_post_content_from_template: function(obj_state, post_dom, root) {
            // Replace the content <div> of a post by its state template

            $this = this;
            var state_template = $('.plebia_post_content_states .plebia_post_'+obj_state, root);
            $('.plebia_post_content', post_dom).html(state_template.html());
        },

        /** STATE: searching ********************/
        update_post_searching: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'searching') {
                $this.set_post_content_from_template('searching', post_dom, root);
            }

            deferred.resolve();

            return deferred.promise();
        },

        /** STATE: downloading ******************/
        update_post_downloading: function(old_state, post_dom, root) {
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

        /** STATE: transcoding_not_ready ********/
        update_post_transcoding_not_ready: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'transcoding_not_ready') {
                $this.set_post_content_from_template('transcoding_not_ready', post_dom, root);

                // Download link on title
                $this.get_post_title(post_dom).done(function(title) {
                    $('.plebia_post_title', post_dom).html(title);

                    $this.get_download_url(post_dom).then(function(url) {
                        $('.plebia_download .video_link').attr('href', url);

                        deferred.resolve();
                    });
                });
            }

            return deferred.promise();
        },

        /** STATE: transcoding_ready ************/
        /*update_post_transcoding_ready: function(old_state, post_dom, root) {
            var $this = this;
            var deferred= $.Deferred();

            // Check if we are entering this state now
            if(old_state != 'transcoding_ready') {
                $this.set_post_content_from_template('transcoding_ready', post_dom, root);

                // Video init
                $.when($this.get_api_object('video', post_dom)).done(function(video) {
                    $this.init_video(video, post_dom, true);

                    deferred.resolve();
                });
            }

            return deferred.promise();
        },*/

        /** STATE: all_ready ********************/
        update_post_all_ready: function(old_state, post_dom, root) {
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

        /** STATE: error ************************/
        update_post_error: function(old_state, post_dom, root) {
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



