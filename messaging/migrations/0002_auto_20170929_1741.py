# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-29 17:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Presence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_name', models.CharField(help_text='Reply channel for the connection', max_length=255)),
                ('staff_key', models.CharField(max_length=32)),
                ('last_seen', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='PresenceGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_name', models.CharField(help_text='Group channel name for this presence group', max_length=255, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='presence',
            name='presence_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='messaging.PresenceGroup'),
        ),
        migrations.AlterUniqueTogether(
            name='presence',
            unique_together=set([('presence_group', 'channel_name')]),
        ),
    ]
