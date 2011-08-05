# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Post.series_season'
        db.delete_column('wall_post', 'series_season_id')

        # Renaming column for 'Post.series_episode' to match new field type.
        db.rename_column('wall_post', 'series_episode', 'series_episode_id')
        # Changing field 'Post.series_episode'
        db.alter_column('wall_post', 'series_episode_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['wall.SeriesSeasonEpisode']))

        # Adding index on 'Post', fields ['series_episode']
        db.create_index('wall_post', ['series_episode_id'])

        # Deleting field 'SeriesSeasonEpisode.series'
        db.delete_column('wall_seriesseasonepisode', 'series_id')

        # Adding field 'SeriesSeasonEpisode.season'
        db.add_column('wall_seriesseasonepisode', 'season', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['wall.SeriesSeason']), keep_default=False)

        # Deleting field 'SeriesSeason.season'
        db.delete_column('wall_seriesseason', 'season')

        # Adding field 'SeriesSeason.number'
        db.add_column('wall_seriesseason', 'number', self.gf('django.db.models.fields.IntegerField')(default=1), keep_default=False)


    def backwards(self, orm):
        
        # Removing index on 'Post', fields ['series_episode']
        db.delete_index('wall_post', ['series_episode_id'])

        # User chose to not deal with backwards NULL issues for 'Post.series_season'
        raise RuntimeError("Cannot reverse this migration. 'Post.series_season' and its values cannot be restored.")

        # Renaming column for 'Post.series_episode' to match new field type.
        db.rename_column('wall_post', 'series_episode_id', 'series_episode')
        # Changing field 'Post.series_episode'
        db.alter_column('wall_post', 'series_episode', self.gf('django.db.models.fields.IntegerField')(null=True))

        # User chose to not deal with backwards NULL issues for 'SeriesSeasonEpisode.series'
        raise RuntimeError("Cannot reverse this migration. 'SeriesSeasonEpisode.series' and its values cannot be restored.")

        # Deleting field 'SeriesSeasonEpisode.season'
        db.delete_column('wall_seriesseasonepisode', 'season_id')

        # User chose to not deal with backwards NULL issues for 'SeriesSeason.season'
        raise RuntimeError("Cannot reverse this migration. 'SeriesSeason.season' and its values cannot be restored.")

        # Deleting field 'SeriesSeason.number'
        db.delete_column('wall_seriesseason', 'number')


    models = {
        'wall.post': {
            'Meta': {'object_name': 'Post'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'series_episode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wall.SeriesSeasonEpisode']"})
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
            'file_path': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['wall']
