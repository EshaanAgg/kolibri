# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-09-14 00:24
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("bookmarks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookmark",
            name="created",
            field=models.DateTimeField(
                db_index=True, default=django.utils.timezone.now
            ),
        ),
    ]
