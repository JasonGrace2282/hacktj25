# Generated by Django 5.1.7 on 2025-03-09 07:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_biasedcontent_accuracy_certainty'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentCreator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='biasedmedia',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='media_set', to='api.contentcreator'),
        ),
    ]
