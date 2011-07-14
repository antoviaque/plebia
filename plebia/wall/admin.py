from wall.models import Post
from django.contrib import admin

class PostAdmin(admin.ModelAdmin):
    list_display = ('series_name', 'series_season', 'series_episode', 'torrent_status', 'torrent_progress', 'pub_date')

admin.site.register(Post, PostAdmin)

