# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Torrent.eta'
        db.alter_column('wall_torrent', 'eta', self.gf('django.db.models.fields.CharField')(max_length=50))


    def backwards(self, orm):
        
        # Changing field 'Torrent.eta'
        db.alter_column('wall_torrent', 'eta', self.gf('django.db.models.fields.CharField')(max_length=20))


    models = {
        'wall.episode': {
            'Meta': {'object_name': 'Episode'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'director': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'first_aired': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'guest_stars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'imdb_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'overview': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'rating': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Season']"}),
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True'}),
            'tvdb_id': ('django.db.models.fields.IntegerField', [], {}),
            'tvdb_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Video']", 'null': 'True'}),
            'watched': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Series']"})
        },
        'wall.season': {
            'Meta': {'object_name': 'Season'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Series']"}),
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True'})
        },
        'wall.series': {
            'Meta': {'object_name': 'Series'},
            'airing_status': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'banner_url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fanart_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'first_aired': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imdb_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'overview': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'poster_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'rating': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'tvcom_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'tvdb_id': ('django.db.models.fields.IntegerField', [], {}),
            'tvdb_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'zap2it_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'wall.torrent': {
            'Meta': {'object_name': 'Torrent'},
            'active_time': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'details_url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'download_speed': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'eta': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'file_list': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'has_metadata': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_status_change': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'peers': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'progress': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'seeds': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'}),
            'tracker_url_list': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'upload_speed': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'wall.tvdbcache': {
            'Meta': {'object_name': 'TVDBCache'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'wall.video': {
            'Meta': {'object_name': 'Video'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_path': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'mp4_path': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'ogv_path': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'original_path': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'}),
            'webm_path': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'})
        }
    }

    complete_apps = ['wall']
