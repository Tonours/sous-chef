# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-12 20:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'verbose_name_plural': 'Notifications'},
        ),
        migrations.AddField(
            model_name='notification',
            name='priority',
            field=models.CharField(choices=[('normal', 'Normal'), ('urgent', 'Urgent')], default='normal', max_length=15),
        ),
        migrations.AlterField(
            model_name='notification',
            name='description',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='member.Member', verbose_name='Member'),
        ),
    ]