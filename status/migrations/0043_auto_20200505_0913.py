# Generated by Django 3.0.5 on 2020-05-05 13:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('status', '0042_auto_20200501_1149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='sub_service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='status.SubService', verbose_name='Sub-Service'),
        ),
    ]
