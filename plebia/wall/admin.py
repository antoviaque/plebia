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

from wall.models import *
from django.contrib import admin


# Admin interfaces ##################################################

# Post ##

class PostInline(admin.TabularInline):
    model = Post

class PostAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['series']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
    ]

admin.site.register(Post, PostAdmin)


# Episode ##

class EpisodeInline(admin.TabularInline):
    model = Episode

class EpisodeAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['season','number','watched']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('TVDB information',  {'fields': ['tvdb_id', 'name', 'overview', 'director', 'guest_stars', 'language', 'rating', 'writer', 'first_aired', 'image_url', 'imdb_id', 'tvdb_last_updated']}),
        ('Files',             {'fields': ['torrent','video']}),
    ]
    list_display = ('season', 'number', 'name')

admin.site.register(Episode, EpisodeAdmin)


# Season ##

class SeasonInline(admin.TabularInline):
    model = Season

class SeasonAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['series','number']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('Files',             {'fields': ['torrent']}),
    ]
    inlines = [EpisodeInline]

admin.site.register(Season, SeasonAdmin)


# Series ##

class SeriesInline(admin.TabularInline):
    model = Series

class SeriesAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['name',]}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('TVDB information',  {'fields': ['tvdb_id', 'overview', 'language', 'rating', 'first_aired', 'airing_status', 'banner_url', 'poster_url', 'fanart_url', 'imdb_id', 'tvcom_id', 'zap2it_id', 'tvdb_last_updated']}),
    ]
    inlines = [SeasonInline]

admin.site.register(Series, SeriesAdmin)


# Torrent ##

class TorrentInline(admin.TabularInline):
    model = Torrent

class TorrentAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['name','hash']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('State information', {'fields': ['status','progress','seeds','peers','type']}),
    ]
    inlines = [SeasonInline, EpisodeInline]
    list_display = ('name', 'status', 'progress', 'seeds', 'peers')

admin.site.register(Torrent, TorrentAdmin)


# Video ##

class VideoInline(admin.TabularInline):
    model = Video

class VideoAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['original_path']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('Transcoding',       {'fields': ['status','image_path','webm_path','mp4_path','ogv_path']}),
    ]
    inlines = [EpisodeInline]

admin.site.register(Video, VideoAdmin)


# TVDBCache ##

class TVDBCacheAdmin(admin.ModelAdmin):
    pass

admin.site.register(TVDBCache, TVDBCacheAdmin)


