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

// Skin ///////////////////////////////////////////////////////////

(function($) {

    $.plebia.skin = function(skin, root) {
        var stream = $('.plebia_stream', root);

        $.each($.plebia.post_state_list, function() {
            var state = this;

            if(state == 'new') {
                return;
            }

            // Copy base template
            var post_dom = $.plebia.new_base_template(stream, root);

            post_dom.addClass('plebia_post_'+state);

            // Post header
            $('.plebia_post_time', post_dom).html('Wed, Aug 3rd - 12:43pm');
            $('.plebia_post_title', post_dom).html(state+' - Season 2, Episode 1');

            // State-speicific update
            $.plebia['update_post_'+state]('new', post_dom, root);
        });
    };

})(jQuery);




