# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Video.file_path'
        db.delete_column('wall_video', 'file_path')

        # Adding field 'Video.original_path'
        db.add_column('wall_video', 'original_path', self.gf('django.db.models.fields.CharField')(default='', max_length=200), keep_default=False)

        # Adding field 'Video.webm_path'
        db.add_column('wall_video', 'webm_path', self.gf('django.db.models.fields.CharField')(default='', max_length=200), keep_default=False)

        # Adding field 'Video.mp4_path'
        db.add_column('wall_video', 'mp4_path', self.gf('django.db.models.fields.CharField')(default='', max_length=200), keep_default=False)

        # Adding field 'Video.ogv_path'
        db.add_column('wall_video', 'ogv_path', self.gf('django.db.models.fields.CharField')(default='', max_length=200), keep_default=False)

        # Adding field 'Video.image_path'
        db.add_column('wall_video', 'image_path', self.gf('django.db.models.fields.CharField')(default='', max_length=200), keep_default=False)


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'Video.file_path'
        raise RuntimeError("Cannot reverse this migration. 'Video.file_path' and its values cannot be restored.")

        # Deleting field 'Video.original_path'
        db.delete_column('wall_video', 'original_path')

        # Deleting field 'Video.webm_path'
        db.delete_column('wall_video', 'webm_path')

        # Deleting field 'Video.mp4_path'
        db.delete_column('wall_video', 'mp4_path')

        # Deleting field 'Video.ogv_path'
        db.delete_column('wall_video', 'ogv_path')

        # Deleting field 'Video.image_path'
        db.delete_column('wall_video', 'image_path')


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
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Video']", 'null': 'True'})
        },
        'wall.torrent': {
            'Meta': {'object_name': 'Torrent'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'peers': ('django.db.models.fields.IntegerField', [], {}),
            'progress': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'seeds': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'})
        },
        'wall.video': {
            'Meta': {'object_name': 'Video'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'mp4_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'ogv_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'original_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'webm_path': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['wall']
