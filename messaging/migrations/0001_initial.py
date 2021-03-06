# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-01 19:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conversation_key', models.CharField(db_index=True, editable=False, max_length=65)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('sender', models.CharField(max_length=32)),
                ('receiver', models.CharField(max_length=32)),
                ('content', models.TextField()),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
