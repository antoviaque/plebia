from tastypie import fields
from tastypie.resources import ModelResource
from wall.models import *


class VideoResource(ModelResource):
    class Meta:
        queryset = Video.objects.all()
        fields = ["date_added","id","image_path","mp4_path","ogv_path","original_path","webm_path"]

class TorrentResource(ModelResource):
    class Meta:
        queryset = Torrent.objects.all()
        fields = ["date_added","hash","id","name","peers","progress","seeds","status"]

class SeriesSeasonEpisodeResource(ModelResource):
    torrent = fields.ForeignKey(TorrentResource, 'torrent', null=True)
    video   = fields.ForeignKey(VideoResource, 'video', null=True)
    class Meta:
        queryset = SeriesSeasonEpisode.objects.all()
        fields = ["id","date_added","name","number","torrent"]

class PostResource(ModelResource):
    episode = fields.ForeignKey(SeriesSeasonEpisodeResource, 'episode')
    class Meta:
        queryset = Post.objects.all()
        fields = ['id','episode','date_added']

