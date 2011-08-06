from django.db import models
from django import forms

TORRENT_STATUSES = (
    ('New', 'New'),
    ('Downloading', 'Downloading'),
    ('Transcoding', 'Transcoding'),
    ('Completed', 'Completed'),
    ('Error', 'Error'),
)

class Torrent(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    hash = models.CharField(max_length=200)
    name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=TORRENT_STATUSES, default='New')
    progress = models.FloatField('progress', default=0)
    seeds = models.IntegerField('seeds')
    peers = models.IntegerField('peers')

class Video(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    original_path = models.CharField(max_length=200)
    webm_path = models.CharField(max_length=200, blank=True)
    mp4_path = models.CharField(max_length=200, blank=True)
    ogv_path = models.CharField(max_length=200, blank=True)
    image_path = models.CharField(max_length=200, blank=True)

class Series(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    name = models.CharField(max_length=200)

class SeriesSeason(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    series = models.ForeignKey(Series)
    torrent = models.ForeignKey(Torrent, null=True)

class SeriesSeasonEpisode(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    number = models.IntegerField('number')
    name = models.CharField('name', max_length=200, blank=True)
    season = models.ForeignKey(SeriesSeason)
    torrent = models.ForeignKey(Torrent, null=True, blank=True)
    video = models.ForeignKey(Video, null=True, blank=True)

class Post(models.Model):
    date_added = models.DateTimeField('date added', auto_now_add=True)
    episode = models.ForeignKey(SeriesSeasonEpisode)

class PostForm(forms.Form):
    name = forms.CharField(max_length=200)
    season = forms.IntegerField('season')
    episode = forms.IntegerField('episode', required=False)


