# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Post'
        db.create_table('wall_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('series_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('series_season', self.gf('django.db.models.fields.IntegerField')()),
            ('series_episode', self.gf('django.db.models.fields.IntegerField')()),
            ('torrent_hash', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('torrent_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('torrent_progress', self.gf('django.db.models.fields.IntegerField')()),
            ('file_path', self.gf('django.db.models.fields.FilePathField')(max_length=200)),
        ))
        db.send_create_signal('wall', ['Post'])


    def backwards(self, orm):
        
        # Deleting model 'Post'
        db.delete_table('wall_post')


    models = {
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'file_path': ('django.db.models.fields.FilePathField', [], {'max_length': '200'}),
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
