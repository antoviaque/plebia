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

def status(request):
    '''Statistics about the operations of the server'''

    # Stats of objects state
    object_stat = list()
    for model_class in [Episode, Video, Torrent]:
        url = "/status/%s/" % model_class.__name__.lower()
        nb_processing = {'value': model_class.processing_objects.count(), 'url': url+'processing/'}
        nb_completed = {'value': model_class.completed_objects.count(), 'url': url+'completed/'}
        nb_error = {'value': model_class.error_objects.count(), 'url': url+'error/'}
        percent_success = {'value': '%.0f' % (nb_completed['value']*100/(nb_completed['value']+nb_error['value'])) + '%', 'url': None}
        object_stat.append([model_class.__name__+'s', nb_processing, nb_completed, nb_error, percent_success])

    # Stats of log messages levels
    import re
    log_stat = list()
    with open(settings.LOG_FILE) as f:
        log = f.read()
        nb_info = len(re.findall(r'\[INFO\]', log))
        nb_warning = len(re.findall(r'\[WARNING\]', log))
        nb_error = len(re.findall(r'\[ERROR\]', log))
        nb_critical = len(re.findall(r'\[CRITICAL\]', log))
        log_stat.append([nb_info, nb_warning, nb_error, nb_critical])

    return render_to_response('wall/status.html', {
        'object_stat': object_stat,
        'log_stat': log_stat,
    }, context_instance=RequestContext(request))

def status_object_detail(request, obj_type, obj_status):
    '''List of objects for a given type & status'''

    if obj_type == 'episode':
        obj_class = Episode
    elif obj_type == 'video':
        obj_class = Video
    elif obj_type == 'torrent':
        obj_class = Torrent

    object_list = getattr(obj_class, '%s_objects' % obj_status).all()

    return render_to_response('wall/status_object_detail.html', {
        'object_list': object_list,
        'obj_type': obj_type,
        'obj_status': obj_status,
    }, context_instance=RequestContext(request))

