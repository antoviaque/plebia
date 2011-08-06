from wall.models import *
from django.contrib import admin

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
        (None,                {'fields': ['name']}),
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
        ('State information', {'fields': ['status','progress','seeds','peers']}),
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
        ('Transcoding',       {'fields': ['image_path','webm_path','mp4_path','ogv_path']}),
    ]
    inlines = [SeriesSeasonEpisodeInline]

admin.site.register(Video, VideoAdmin)


