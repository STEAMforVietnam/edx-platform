# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-10 13:57


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0019_consolidate_slug'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oauth2providerconfig',
            name='provider_slug',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='idp_slug',
        ),
    ]
