# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Consumer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('key', models.CharField(unique=True, max_length=255)),
                ('secret', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EnvironmentMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Ensure the environment name has not been used before.', unique=True, max_length=255, verbose_name=b'LTI Environment Name')),
                ('sdios_environment_uuid', models.CharField(unique=True, max_length=36)),
                ('lti_environment_key', models.CharField(unique=True, max_length=255, verbose_name=b'LTI Environment Key')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sdios_url', models.CharField(default=b'127.0.0.1:8000', help_text=b'This is where your SDI OS instance lives.', max_length=255, verbose_name=b' URL')),
                ('sdios_username', models.CharField(default=b'', help_text=b'The username of your SDI OS API user.', max_length=255, verbose_name=b'SDI OS API username')),
                ('sdios_password', models.CharField(default=b'', help_text=b'The password of your SDI OS API user.', max_length=255, verbose_name=b'SDI OS API password')),
                ('client_id', models.CharField(default=b'', help_text=b'Client ID found under API application at {SDI OS URL}/api/o/applications.', max_length=255, verbose_name=b'Client ID')),
                ('client_secret', models.CharField(default=b'', help_text=b'Client Secret found under API application at {SDI OS URL}/api/o/applications.', max_length=255, verbose_name=b'Client Secret')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lti_user_id', models.CharField(max_length=255)),
                ('sdios_username', models.CharField(unique=True, max_length=255)),
                ('sdios_password', models.CharField(max_length=255)),
                ('consumer', models.ForeignKey(to='sdios_lti.Consumer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='usermap',
            unique_together=set([('consumer', 'lti_user_id')]),
        ),
    ]
