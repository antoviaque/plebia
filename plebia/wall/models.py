from django.db import models
from django.forms import ModelForm

TORRENT_STATUSES = (
    ('New', 'New'),
    ('Downloading', 'Downloading'),
    ('Completed', 'Completed'),
    ('Not found', 'Not found'),
    ('Error', 'Error'),
)

class Post(models.Model):
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    series_name = models.CharField(max_length=200)
    series_season = models.IntegerField('season')
    series_episode = models.IntegerField('episode')
    torrent_hash = models.CharField(max_length=200, blank=True)
    torrent_name = models.CharField(max_length=200, blank=True)
    torrent_status = models.CharField(max_length=20, choices=TORRENT_STATUSES, default='New')
    torrent_progress = models.IntegerField('progress', default=0)
    file_path = models.CharField(max_length=200, blank=True)

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('series_name', 'series_season', 'series_episode')

