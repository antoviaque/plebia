
function update() {
    // Do this synchronously to avoid iterating before the updates have been retreived
    //$.ajaxSetup({async:false});
    // Iter over the posts in progress to update the progress bar every 3 seconds
    $('.stream .stream_post_in_progress').each(function() {
        element = this;
        var id = $(element).attr('id').substring(5);
        $.getJSON("/ajax/post_detail/"+id+"/", function(data) {
            torrent_progress = Math.round(data[0].fields.torrent_progress*100)/100;
            torrent_status = data[0].fields.torrent_status;

            // If download is over, play the video after 5 seconds
            if(torrent_status == 'Completed') {
                $(element).removeClass('stream_post_in_progress');
                setTimeout(function() { // Give time for the transcoding to take some advance
                    $('.post_content', element).load('/ajax/video/'+id+'/', function() {
                        video = $("#post_"+id+"_video");
                        video.VideoJS({
                            controlsBelow: false, // Display control bar below video instead of in front of
                            controlsHiding: true, // Hide controls when mouse is not over the video
                            defaultVolume: 0.85, // Will be overridden by user's last volume if available
                            flashVersion: 9, // Required flash version for fallback
                            linksHiding: true // Hide download links when video is supported
                        });

                        // Play it if no other video has been started on the page
                        $('video').each(function() {
                            video_curr_time = $(this)[0].player.currentTime();
                            if(video_curr_time > 0.0) {
                                $('.stream').addClass('no_auto_play');
                            }
                        });
                        if(!$('.stream').hasClass('no_auto_play')) {
                            video[0].player.play();
                        }
                    });
                }, 5000);
            } else { // Otherwise update the progress bar
                if(torrent_progress > 99) {
                    $('.torrent_status', element).html('Preparing to stream...');
                    $('.torrent_progress', element).css('display', 'none');
                } else if(torrent_progress > 1) {
                    $('.torrent_status', element).html('Downloading the video...');
                    $('.torrent_progress', element).css('display', 'inline');
                }
                    
                $('.torrent_progress_percent', element).html(torrent_progress);
                $('.torrent_progress_bar', element).progressbar('option', 'value', Math.round(torrent_progress));
            }
        });
    });
    setTimeout("update()", 3000);
}

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
    $("#id_series_name").suggest({type:'/tv/tv_program'});

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
    update();

    // Add feedback tab
    var uv = document.createElement('script'); uv.type = 'text/javascript'; uv.async = true;
    uv.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'widget.uservoice.com/6PhXO6580egdGy3eefwsAg.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(uv, s);
});
