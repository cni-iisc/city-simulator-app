# Generated by Django 3.2.9 on 2021-11-12 17:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cityinstantiation',
            name='prg_np_random_state_bin',
        ),
    ]
