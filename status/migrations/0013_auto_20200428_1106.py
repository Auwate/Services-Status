# Generated by Django 3.0.5 on 2020-04-28 15:06

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('status', '0012_auto_20200428_1105'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emaildomainlist',
            old_name='email_domain_description',
            new_name='description',
        ),
    ]
