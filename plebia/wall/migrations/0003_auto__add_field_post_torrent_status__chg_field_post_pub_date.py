# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Post.torrent_status'
        db.add_column('wall_post', 'torrent_status', self.gf('django.db.models.fields.CharField')(default='New', max_length=20), keep_default=False)

        # Changing field 'Post.pub_date'
        db.alter_column('wall_post', 'pub_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))


    def backwards(self, orm):
        
        # Deleting field 'Post.torrent_status'
        db.delete_column('wall_post', 'torrent_status')

        # Changing field 'Post.pub_date'
        db.alter_column('wall_post', 'pub_date', self.gf('django.db.models.fields.DateTimeField')())


    models = {
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'file_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'series_episode': ('django.db.models.fields.IntegerField', [], {}),
            'series_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'series_season': ('django.db.models.fields.IntegerField', [], {}),
            'torrent_hash': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'torrent_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'torrent_progress': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'torrent_status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'})
        }
    }

    complete_apps = ['wall']
