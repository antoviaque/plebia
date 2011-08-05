
// Updates the progress bar of the posts with a download in progress
// and show the video once it is done
function update_progress() {
    // Count the elements to invoke the the next update only after the each() loop is finished
    var elems = $('.stream .stream_post_in_progress');
    var count = elems.length;

    // Iter over the posts in progress to update the progress bar every x seconds
    elems.each(function() {
        var id = $(this).attr('id').substring(5);
        var element = this;
        var torrent_api_url = $('input.torrent_api_url', element).attr('value');

        $.getJSON(torrent_api_url, function(torrent) {
            torrent.progress = Math.round(torrent.progress*100)/100;

            // If transcoding is still in progress, mark the post so that the transcoding loop
            // can refresh it when it's done
            if(torrent.status == 'Transcoding') {
                $(element).addClass('stream_post_transcoding_in_progress'); 
            }

            // If download is over, play the video after 5 seconds
            if(torrent.status == 'Completed' || torrent.status == 'Transcoding') {
                // Make sure we don't do this twice
                $(element).removeClass('stream_post_in_progress'); 

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
            } else { // Otherwise update the progress bar
                if(torrent.progress > 99) {
                    $('.torrent_status', $(element)).html('Preparing to stream...');
                    $('.torrent_progress', $(element)).css('display', 'none');
                } else if(torrent.progress > 1) {
                    $('.torrent_status', $(element)).html('Downloading the video...');
                    $('.torrent_progress', $(element)).css('display', 'inline');
                }
                    
                $('.torrent_progress_percent', $(element)).html(torrent.progress);
                $('.torrent_progress_bar', $(element)).progressbar('option', 'value', Math.round(torrent.progress));
            }
        });

        // Call update_progress() again x seconds after the last each()
        if(!--count) setTimeout("update_progress()", 2000);
    });
}

// Update the video and warning once the transcoding is done by monitoring all 
// elements currently being transcoded
function update_transcoding() {
    // Count the elements to invoke the the next update only after the each() loop is finished
    var elems = $('.stream .stream_post_transcoding_in_progress');
    var count = elems.length;

    if(count == 0) { // no transcoding found - still keep looking for them, as some could be downloading
        setTimeout("update_transcoding()", 10000);
    }

    // Iter over the posts with transcoding in progress
    elems.each(function() {
        var id = $(this).attr('id').substring(5);
        var element = this;
        var torrent_api_url = $('input.torrent_api_url', element).attr('value');

        $.getJSON(torrent_api_url, function(torrent) {
            if(torrent.status == 'Completed') {
                // Make sure we don't do this twice
                $(element).removeClass('stream_post_transcoding_in_progress'); 

                // Don't reload the video automatically if it is paused
                if($('video', element)[0].player.paused()) {
                    show_video(id);
                } else { // Otherwise simply update the warning
                    $('.video_transcoding_in_progress', element).css('display', 'none');
                    $('.video_transcoding_done', element).css('display', 'block');

                    // Allow the user to reload the video himself (and then autoplay)
                    $('.video_transcoding_done a', element).click(function() {
                        show_video(id, function(player) {
                            player.play();
                        });
                    });
                }
            }
        });

        // Call update_progress() again x seconds after the last each()
        if(!--count) setTimeout("update_transcoding()", 5000);
    });
}

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

// Main /////////////////
$(function() {
    // Dress buttons
    $('input:submit').button();

    // Dress progress bars
    $(".torrent_progress_bar").each(function() {
        $(this).progressbar({
            value: Math.round($(this).attr('data'))
        });
    });

    // Load auto-suggest
    $("#id_name").suggest({type:'/tv/tv_program'});

    // Load all videos on the page
    var myManyPlayers = VideoJS.setup("All", {
        controlsBelow: false, // Display control bar below video instead of in front of
        controlsHiding: true, // Hide controls when mouse is not over the video
        defaultVolume: 0.85, // Will be overridden by user's last volume if available
        flashVersion: 9, // Required flash version for fallback
        linksHiding: true // Hide download links when video is supported
    });

    // Next episode link submits a form
    $('.stream_post .next_episode a').click(function(){
        $(this).parent().submit();
        return false;
    });

    // Start page refreshes
    update_progress();
    update_transcoding();

    // Add feedback tab
    var uv = document.createElement('script'); uv.type = 'text/javascript'; uv.async = true;
    uv.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'widget.uservoice.com/6PhXO6580egdGy3eefwsAg.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(uv, s);
});
