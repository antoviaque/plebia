# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'SeriesSeasonEpisode'
        db.delete_table('wall_seriesseasonepisode')

        # Deleting model 'SeriesSeason'
        db.delete_table('wall_seriesseason')

        # Adding model 'Season'
        db.create_table('wall_season', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('series', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Series'])),
            ('torrent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Torrent'], null=True)),
        ))
        db.send_create_signal('wall', ['Season'])

        # Adding model 'Episode'
        db.create_table('wall_episode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('season', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Season'])),
            ('torrent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Torrent'], null=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Video'], null=True)),
            ('tvdb_id', self.gf('django.db.models.fields.IntegerField')()),
            ('overview', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('director', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('guest_stars', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('rating', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('writer', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('first_aired', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('image_url', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('imdb_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('tvdb_last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('watched', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('wall', ['Episode'])

        # Adding model 'TVDBCache'
        db.create_table('wall_tvdbcache', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('time', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('wall', ['TVDBCache'])

        # Adding field 'Series.rating'
        db.add_column('wall_series', 'rating', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Series.airing_status'
        db.add_column('wall_series', 'airing_status', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True), keep_default=False)

        # Adding field 'Series.poster_url'
        db.add_column('wall_series', 'poster_url', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Series.fanart_url'
        db.add_column('wall_series', 'fanart_url', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Series.tvcom_id'
        db.add_column('wall_series', 'tvcom_id', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Series.zap2it_id'
        db.add_column('wall_series', 'zap2it_id', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'Series.tvdb_last_updated'
        db.add_column('wall_series', 'tvdb_last_updated', self.gf('django.db.models.fields.DateTimeField')(null=True), keep_default=False)

        # Changing field 'Series.imdb_id'
        db.alter_column('wall_series', 'imdb_id', self.gf('django.db.models.fields.CharField')(max_length=50))


    def backwards(self, orm):
        
        # Adding model 'SeriesSeasonEpisode'
        db.create_table('wall_seriesseasonepisode', (
            ('next_episode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.SeriesSeasonEpisode'], null=True, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Video'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('season', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.SeriesSeason'])),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('torrent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Torrent'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('wall', ['SeriesSeasonEpisode'])

        # Adding model 'SeriesSeason'
        db.create_table('wall_seriesseason', (
            ('series', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Series'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('torrent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wall.Torrent'], null=True)),
        ))
        db.send_create_signal('wall', ['SeriesSeason'])

        # Deleting model 'Season'
        db.delete_table('wall_season')

        # Deleting model 'Episode'
        db.delete_table('wall_episode')

        # Deleting model 'TVDBCache'
        db.delete_table('wall_tvdbcache')

        # Deleting field 'Series.rating'
        db.delete_column('wall_series', 'rating')

        # Deleting field 'Series.airing_status'
        db.delete_column('wall_series', 'airing_status')

        # Deleting field 'Series.poster_url'
        db.delete_column('wall_series', 'poster_url')

        # Deleting field 'Series.fanart_url'
        db.delete_column('wall_series', 'fanart_url')

        # Deleting field 'Series.tvcom_id'
        db.delete_column('wall_series', 'tvcom_id')

        # Deleting field 'Series.zap2it_id'
        db.delete_column('wall_series', 'zap2it_id')

        # Deleting field 'Series.tvdb_last_updated'
        db.delete_column('wall_series', 'tvdb_last_updated')

        # Changing field 'Series.imdb_id'
        db.alter_column('wall_series', 'imdb_id', self.gf('django.db.models.fields.CharField')(max_length=500))


    models = {
        'wall.episode': {
            'Meta': {'object_name': 'Episode'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'director': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'first_aired': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'guest_stars': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'imdb_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'overview': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'rating': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'season': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Season']"}),
            'torrent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Torrent']", 'null': 'True'}),
            'tvdb_id': ('django.db.models.fields.IntegerField', [], {}),
            'tvdb_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.Video']", 'null': 'True'}),
            'watched': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writer': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
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
            'imdb_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'overview': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'poster_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'rating': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'tvcom_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'tvdb_id': ('django.db.models.fields.IntegerField', [], {}),
            'tvdb_last_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'zap2it_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'wall.torrent': {
            'Meta': {'object_name': 'Torrent'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'download_speed': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'eta': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'peers': ('django.db.models.fields.IntegerField', [], {}),
            'progress': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'seeds': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'New'", 'max_length': '20'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'upload_speed': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        },
        'wall.tvdbcache': {
            'Meta': {'object_name': 'TVDBCache'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {})
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
