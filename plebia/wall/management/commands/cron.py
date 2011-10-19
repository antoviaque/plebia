#
# Copyright (C) 2011 Xavier Antoviaque <xavier@antoviaque.org>
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#

# Includes ##########################################################

import time
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from plebia.wall.downloadmanager import DownloadManager

# Globals ###########################################################

DELAY = 5


# Main ##############################################################

class Command(BaseCommand):
    help = 'Run cron tasks for the given category'
    option_list = BaseCommand.option_list + (
        make_option('-n', '--no-repeat', action="store_false", dest='repeat', default=True,
            help='Do not repeat every few seconds for one minute, execute just once'),
        )

    def handle(self, *args, **options):
        dl_manager = DownloadManager()

        if len(args) != 1 or args[0] not in dl_manager.get_actions_list():
            raise CommandError('You must specify one valid command (%s)' % repr(dl_manager.get_actions_list()))

        command = args[0]
        repeat = options.get('repeat', True)

        if not repeat:
            dl_manager.do(command)
        else:
            # Runs the specified action, every DELAY seconds for 1 minute
            start = time.time()
            next = start
            while next <= start+50-DELAY:
                dl_manager.do(command)

                next += DELAY
                sleep_time = next - time.time()
                if sleep_time > 0:
                    time.sleep(next - time.time())
            


