# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Torrent.download_speed'
        db.add_column('wall_torrent', 'download_speed', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Torrent.upload_speed'
        db.add_column('wall_torrent', 'upload_speed', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'Torrent.eta'
        db.add_column('wall_torrent', 'eta', self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Torrent.download_speed'
        db.delete_column('wall_torrent', 'download_speed')

        # Deleting field 'Torrent.upload_speed'
        db.delete_column('wall_torrent', 'upload_speed')

        # Deleting field 'Torrent.eta'
        db.delete_column('wall_torrent', 'eta')


    models = {
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'episode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.SeriesSeasonEpisode']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'wall.series': {
            'Meta': {'object_name': 'Series'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'wall.seriesseason': {
            'Meta': {'object_name': 'SeriesSeason'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Series']"}),
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True'})
        },
        'wall.seriesseasonepisode': {
            'Meta': {'object_name': 'SeriesSeasonEpisode'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.SeriesSeason']"}),
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Video']", 'null': 'True', 'blank': 'True'})
        },
        'wall.torrent': {
            'Meta': {'object_name': 'Torrent'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download_speed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'eta': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'peers': ('django.db.models.fields.IntegerField', [], {}),
            'progress': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'seeds': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'upload_speed': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'wall.video': {
            'Meta': {'object_name': 'Video'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'mp4_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'ogv_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'original_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'}),
            'webm_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['wall']
