//
// Copyright (C) 2011 Xavier Antoviaque <xavier@antoviaque.org>
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

// Update loops /////////////////////////////////////////////////////

// Updates the progress bar of the posts with a download in progress
function torrent_update() {
    // Count the elements to invoke the the next update only after the each() loop is finished
    var elems = $('.stream .stream_post_torrent_update');
    var count = elems.length;

    // Iter over the posts in progress to update the progress bar every x seconds
    elems.each(function() {
        var id = $(this).attr('id').substring(5);
        var element = this;
        var torrent_api_url = $('input.torrent_api_url', element).val();

        $.getJSON(torrent_api_url, function(torrent) {
            // Update progression %
            torrent.progress = Math.round(torrent.progress*100)/100;
            $('.torrent_progress_percent', element).html(torrent.progress);
            $('.torrent_progress_bar', element).progressbar('option', 'value', Math.round(torrent.progress));

            // Update status message
            if(torrent.progress > 99) {
                $('.torrent_status', element).html('Preparing to stream...');
                $('.torrent_progress', element).css('display', 'none');
            } else if(torrent.progress > 1) {
                $('.torrent_status', element).html('Downloading the video...');
                $('.torrent_progress', element).css('display', 'inline');
            }

            // Once the download is completed, switch to the video_update() loop
            if(torrent.status == 'Completed') {
                $(element).addClass('stream_post_video_update'); 
                $(element).removeClass('stream_post_torrent_update'); 
            }
        });

        // Call update_progress() again x seconds after the last each()
        if(!--count) setTimeout("torrent_update()", 2000);
    });
}

// Show the video when transcoding starts, update the video and warning once the transcoding 
// is done by monitoring all elements after the torrent download finished
function video_update() {
    // Count the elements to invoke the the next update only after the each() loop is finished
    var elems = $('.stream .stream_post_video_update');
    var count = elems.length;

    if(count == 0) { // no transcoding found - still keep looking for them, as some could be downloading
        setTimeout("video_update()", 10000);
    }

    // Iter over the posts with transcoding in progress
    elems.each(function() {
        var id = $(this).attr('id').substring(5);
        var element = this;
        var video_dom = $('video', element);
        
        // If the video API url is not on the DOM, try to get it through the API
        // (the video object is only created once the files are available)
        var video_api_url = $('input.video_api_url', element).val();
        if(!video_api_url) {
            // The reference to the video is stored on the episode object
            var episode_api_url = $('input.episode_api_url', element).val();
            $.getJSON(episode_api_url, function(episode) {
                if(episode.video) {
                    $('input.video_api_url', element).val(episode.video);
                }
            });
        // And then wait for the API request to complete before querying the video object
        } else {
            $.getJSON(video_api_url, function(video) {
                // If the transcoding hasn't started yet, inform about it
                if(video.status == 'New') {
                    $('.torrent_status', element).html('Streaming queued, please wait...');
                    $('.torrent_progress', element).css('display', 'none');
                }
                // If the video is available and not loaded already, load it
                else if(video_dom.length == 0 && (video.status == 'Transcoding' || video.status == 'Completed')) {
                    setTimeout(function() { // Give time for the transcoding to take some advance
                        // Load the video and play it automatically
                        show_video(id, function(player) {
                            // Play only if no other video is currently playing
                            var elems = $('video');
                            var count = elems.length;
                            $('video').each(function() {
                                if(!$(this)[0].player.paused()) {
                                    $('.stream').addClass('no_auto_play');
                                }
                                if(!--count && !$('.stream').hasClass('no_auto_play')) {
                                    player.play();
                                    $('.stream').removeClass('no_auto_play');
                                }
                            });
                        });
                    }, 5000);
                // Clean-up when video transcoding is completed and <video> dom is loaded
                } else if(video.status == 'Completed') {
                    // Only reload the video automatically (to be able to seek/pause/etc.) if it is not playing
                    if($('video', element)[0].player.paused()) {
                        show_video(id);
                    // Otherwise simply update the warning
                    } else { 
                        $('.video_transcoding_in_progress', element).css('display', 'none');
                        $('.video_transcoding_done', element).css('display', 'block');

                        // and allow the user to reload the video himself
                        $('.video_transcoding_done a', element).click(function() {
                            show_video(id, function(player) {
                                player.play();
                            });
                        });
                    }

                    // End monitoring of this video
                    $(element).removeClass('stream_post_video_update'); 
                }
            });
        }

        // Call update_progress() again x seconds after the last each()
        if(!--count) setTimeout("video_update()", 5000);
    });
}


// Helpers //////////////////////////////////////////////////////////

// Ajax loading of a video
function show_video(id, callback) {
    var element = $('#post_'+id);
    $('.post_content', element).load('/ajax/video/'+id+'/', function() {
        var video = $("#post_"+id+"_video");
        video.VideoJS({
            controlsBelow: false, // Display control bar below video instead of in front of
            controlsHiding: true, // Hide controls when mouse is not over the video
            defaultVolume: 0.85, // Will be overridden by user's last volume if available
            flashVersion: 9, // Required flash version for fallback
            linksHiding: true // Hide download links when video is supported
        });

        if(callback) {
            callback(video[0].player);
        }
    });
}


// Main /////////////////////////////////////////////////////////////

$(function() {
    // Dress progress bars
    $(".torrent_progress_bar").each(function() {
        $(this).progressbar({
            value: Math.round($(this).attr('data'))
        });
    });

    // Load all videos on the page
    var myManyPlayers = VideoJS.setup("All", {
        controlsBelow: false, // Display control bar below video instead of in front of
        controlsHiding: true, // Hide controls when mouse is not over the video
        defaultVolume: 0.85, // Will be overridden by user's last volume if available
        flashVersion: 9, // Required flash version for fallback
        linksHiding: true // Hide download links when video is supported
    });

    // Start page refreshes
    torrent_update();
    video_update();

});

