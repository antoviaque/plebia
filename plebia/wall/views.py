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
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.core import serializers
from django.utils import simplejson

from wall.models import *


# Logging ###########################################################

from plebia.log import get_logger
log = get_logger(__name__)


# Views #############################################################

def index(request):
    return render_to_response('wall/index.html', {
        'form': PostForm(),
    }, context_instance=RequestContext(request))


def ajax_search(request, search_string):
    '''Perform a search in the db on the series before returning results'''

    # Create all new series objects matching search_string on TVDB
    Series.objects.add_by_search(search_string)

    # Build a list of matching series (larger set than the one returned by TVDB, 
    # which only contains entire word matches
    series_list = Series.objects.filter(name__icontains=search_string).order_by('-first_aired')[:20]
    
    log.info('Series found for live search "%s" => %s', search_string, series_list)

    return render_to_response('wall/search.html', {
        'series_list': series_list,
    }, context_instance=RequestContext(request))


def ajax_new_post(request, series_id):
    '''Add a new post to the feed'''

    log.info('New post for series_id=%d', series_id)

    series = Series.objects.get(id=series_id)
    # Make sure the series info and related seasons & episodes are up to date
    series.update_from_tvdb()

    post = Post(series=series)
    post.save()

    return HttpResponse(simplejson.dumps(['/api/v1/post/%d/' % post.id,]))


