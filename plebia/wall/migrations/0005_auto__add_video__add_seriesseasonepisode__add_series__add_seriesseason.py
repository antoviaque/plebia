# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Video'
        db.create_table('wall_video', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('file_path', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('wall', ['Video'])

        # Adding model 'SeriesSeasonEpisode'
        db.create_table('wall_seriesseasonepisode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('series', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.SeriesSeason'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('torrent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Torrent'], null=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Video'], null=True)),
        ))
        db.send_create_signal('wall', ['SeriesSeasonEpisode'])

        # Adding model 'Series'
        db.create_table('wall_series', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('wall', ['Series'])

        # Adding model 'SeriesSeason'
        db.create_table('wall_seriesseason', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('series', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Series'])),
            ('season', self.gf('django.db.models.fields.IntegerField')()),
            ('torrent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Torrent'], null=True)),
        ))
        db.send_create_signal('wall', ['SeriesSeason'])

        # Adding model 'Torrent'
        db.create_table('wall_torrent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('hash', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='New', max_length=20)),
            ('progress', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('seeds', self.gf('django.db.models.fields.IntegerField')()),
            ('peers', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('wall', ['Torrent'])

        # Deleting field 'Post.series_name'
        db.delete_column('wall_post', 'series_name')

        # Deleting field 'Post.torrent_progress'
        db.delete_column('wall_post', 'torrent_progress')

        # Deleting field 'Post.torrent_name'
        db.delete_column('wall_post', 'torrent_name')

        # Deleting field 'Post.torrent_status'
        db.delete_column('wall_post', 'torrent_status')

        # Deleting field 'Post.torrent_hash'
        db.delete_column('wall_post', 'torrent_hash')

        # Deleting field 'Post.file_path'
        db.delete_column('wall_post', 'file_path')

        # Renaming column for 'Post.series_season' to match new field type.
        db.rename_column('wall_post', 'series_season', 'series_season_id')
        # Changing field 'Post.series_season'
        db.alter_column('wall_post', 'series_season_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.SeriesSeason']))

        # Adding index on 'Post', fields ['series_season']
        db.create_index('wall_post', ['series_season_id'])

        # Changing field 'Post.series_episode'
        db.alter_column('wall_post', 'series_episode', self.gf('django.db.models.fields.IntegerField')(null=True))


    def backwards(self, orm):
        
        # Removing index on 'Post', fields ['series_season']
        db.delete_index('wall_post', ['series_season_id'])

        # Deleting model 'Video'
        db.delete_table('wall_video')

        # Deleting model 'SeriesSeasonEpisode'
        db.delete_table('wall_seriesseasonepisode')

        # Deleting model 'Series'
        db.delete_table('wall_series')

        # Deleting model 'SeriesSeason'
        db.delete_table('wall_seriesseason')

        # Deleting model 'Torrent'
        db.delete_table('wall_torrent')

        # User chose to not deal with backwards NULL issues for 'Post.series_name'
        raise RuntimeError("Cannot reverse this migration. 'Post.series_name' and its values cannot be restored.")

        # Adding field 'Post.torrent_progress'
        db.add_column('wall_post', 'torrent_progress', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Post.torrent_name'
        db.add_column('wall_post', 'torrent_name', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Post.torrent_status'
        db.add_column('wall_post', 'torrent_status', self.gf('django.db.models.fields.CharField')(default='New', max_length=20), keep_default=False)

        # Adding field 'Post.torrent_hash'
        db.add_column('wall_post', 'torrent_hash', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Post.file_path'
        db.add_column('wall_post', 'file_path', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Renaming column for 'Post.series_season' to match new field type.
        db.rename_column('wall_post', 'series_season_id', 'series_season')
        # Changing field 'Post.series_season'
        db.alter_column('wall_post', 'series_season', self.gf('django.db.models.fields.IntegerField')())

        # User chose to not deal with backwards NULL issues for 'Post.series_episode'
        raise RuntimeError("Cannot reverse this migration. 'Post.series_episode' and its values cannot be restored.")


    models = {
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'series_episode': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'series_season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.SeriesSeason']"})
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
            'season': ('django.db.models.fields.IntegerField', [], {}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Series']"}),
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True'})
        },
        'wall.seriesseasonepisode': {
            'Meta': {'object_name': 'SeriesSeasonEpisode'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.SeriesSeason']"}),
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
            'file_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['wall']
