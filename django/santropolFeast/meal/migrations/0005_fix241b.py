# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-03 11:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meal', '0004_fix004d'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='component_group',
            field=models.CharField(choices=[('main_dish', 'Main Dish'), ('dessert', 'Dessert'), ('diabetic', 'Diabetic Dessert'), ('fruit_salad', 'Fruit Salad'), ('green_salad', 'Green Salad'), ('pudding', 'Pudding'), ('compote', 'Compote')], max_length=100, verbose_name='component group'),
        ),
        migrations.AlterField(
            model_name='component',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='ingredient_group',
            field=models.CharField(choices=[('meat', 'Meat'), ('dairy', 'Dairy'), ('fish', 'Fish'), ('seafood', 'Seafood'), ('veggies_and_fruits', 'Veggies and fruits'), ('legumineuse', 'Legumineuse'), ('grains', 'Grains'), ('fresh_herbs', 'Fresh herbs'), ('spices', 'Spices'), ('dry_and_canned_goods', 'Dry and canned goods'), ('oils_and_sauces', 'Oils and sauces')], max_length=100, verbose_name='ingredient group'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=50, unique=True, verbose_name='name'),
        ),
    ]
