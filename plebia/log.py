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
import logging, logging.handlers
import sys, traceback

# Init ##############################################################

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', \
                    datefmt='%m/%d/%Y %I:%M:%S %p', \
                    level=settings.LOG_LEVEL, \
                    filename=settings.LOG_FILE)

# Set sane levels of logging for external modules
import south.logger
logging.getLogger('south').setLevel(logging.INFO)

# Functions #########################################################

def get_logger(name):
    """Return the logger for the provided name (usually __name__ of calling module)"""

    log = logging.getLogger(name)

    # Raise exceptions for important log issues in DEBUG mode
    if settings.RAISE_EXCEPTION_ON_ERROR:
        logging.handlers.ExceptionRaiserHandler = ExceptionRaiserHandler
        handler = logging.handlers.ExceptionRaiserHandler()
        handler.setLevel(logging.ERROR) # Only for WARN & CRITICAL log messages
        log.addHandler(handler)

    return log

def handle_exception(exc_type, exc_value, exc_traceback):
    """Used by cron processes, django only automatically catches exceptions for HTTP requests"""

    log = get_logger(__name__)
    formatted_exception = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log.critical("Uncaught exception:\n"+formatted_exception)
    sys.exit(1)

def catch_exceptions():
    '''Install handler for exceptions'''
    
    sys.excepthook = handle_exception


# Handlers ##########################################################

class ExceptionRaiserHandler(logging.Handler):
    '''Raise exception when a message is handled by this handler
    To allow developers to not let important issues go through unnoticed, for example in unit tests'''
    
    def emit(self, record):
        if sys.exc_info()[0] is not None:
            # If there is already an exception in the current context, let it propagate
            raise
        else:
            raise Exception(record.getMessage())

