# -*- coding: utf-8 -*-
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

import time, os
from optparse import make_option
from mercurial import lock, error

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from plebia.wall.downloadmanager import DownloadManager


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Globals ###########################################################

DELAY = 5
MAX_RUN_TIME=50 # seconds


# Main ##############################################################

class Command(BaseCommand):
    help = 'Run cron tasks for the given category'
    option_list = BaseCommand.option_list + (
        make_option('-n', '--no-repeat', action="store_false", dest='repeat', default=True,
            help='Do not repeat every few seconds for one minute, execute just once'),
        )

    def __init__(self):
        super(self.__class__,self).__init__()

        self.dl_manager = DownloadManager()
        self.start = time.time()

    def handle(self, *args, **options):

        if len(args) != 1 or args[0] not in self.dl_manager.get_actions_list():
            raise CommandError('You must specify one valid command (%s)' % repr(self.dl_manager.get_actions_list()))

        command = args[0]
        repeat = options.get('repeat', True)

        # Only allow one cron process per command to run at a single time
        lock_path = os.path.join(settings.LOCK_PATH, '.%s.pid' % command)
        try:
            l = lock.lock(lock_path, timeout=MAX_RUN_TIME) # wait at most 50s
            self.do(command, repeat)
        except error.LockHeld:
            log.debug("Active process for command '%s', aborting.", command)
        else:
            l.release()

    def do(self, command, repeat):
        '''Run the specified action (once or repeat=True for a time-limited loop)'''

        log.debug("Running download manager for command '%s' (repeat=%d)", command, repeat)

        if not repeat:
            self.dl_manager.do(command)
        else:
            # Runs the specified action, every DELAY seconds for 1 minute
            stop_time = self.start + MAX_RUN_TIME - DELAY
            while time.time() <= stop_time:
                self.dl_manager.do(command)
                time.sleep(DELAY)
            


