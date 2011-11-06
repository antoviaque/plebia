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

from django.conf import settings
import logging, sys, traceback

# Init ##############################################################

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', \
                    datefmt='%m/%d/%Y %I:%M:%S %p', \
                    level=settings.LOG_LEVEL, \
                    filename=settings.LOG_FILE)

# Functions #########################################################

def get_logger(name):
    return logging.getLogger(name)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Used by cron processes, for which exceptions aren't automatically caught'"""

    log = get_logger(__name__)
    formatted_exception = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log.critical("Uncaught exception:\n"+formatted_exception)
    sys.exit(1)

def catch_exceptions():
    '''Install handler for exceptions'''
    
    sys.excepthook = handle_exception
