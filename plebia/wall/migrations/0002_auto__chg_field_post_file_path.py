# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Post.file_path'
        db.alter_column('wall_post', 'file_path', self.gf('django.db.models.fields.CharField')(max_length=200))


    def backwards(self, orm):
        
        # Changing field 'Post.file_path'
        db.alter_column('wall_post', 'file_path', self.gf('django.db.models.fields.FilePathField')(max_length=200))


    models = {
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'file_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'series_episode': ('django.db.models.fields.IntegerField', [], {}),
            'series_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'series_season': ('django.db.models.fields.IntegerField', [], {}),
            'torrent_hash': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'torrent_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'torrent_progress': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['wall']
