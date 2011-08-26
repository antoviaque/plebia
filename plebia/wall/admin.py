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
        (None,                {'fields': ['episode']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
    ]

admin.site.register(Post, PostAdmin)


# SeriesSeasonEpisode ##

class SeriesSeasonEpisodeInline(admin.TabularInline):
    model = SeriesSeasonEpisode

class SeriesSeasonEpisodeAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['season','number','name']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('Files',             {'fields': ['torrent','video']}),
    ]
    inlines = [PostInline]
    list_display = ('season', 'number', 'name')

admin.site.register(SeriesSeasonEpisode, SeriesSeasonEpisodeAdmin)


# SeriesSeason ##

class SeriesSeasonInline(admin.TabularInline):
    model = SeriesSeason

class SeriesSeasonAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['series','number']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
        ('Files',             {'fields': ['torrent']}),
    ]
    inlines = [SeriesSeasonEpisodeInline]

admin.site.register(SeriesSeason, SeriesSeasonAdmin)


# Series ##

class SeriesInline(admin.TabularInline):
    model = Series

class SeriesAdmin(admin.ModelAdmin):
    readonly_fields = ("date_added",)
    fieldsets = [
        (None,                {'fields': ['name','url']}),
        ('Date information',  {'fields': ['date_added'], 'classes': ['collapse']}),
    ]
    inlines = [SeriesSeasonInline]

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
    inlines = [SeriesSeasonInline, SeriesSeasonEpisodeInline]
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
    inlines = [SeriesSeasonEpisodeInline]

admin.site.register(Video, VideoAdmin)


