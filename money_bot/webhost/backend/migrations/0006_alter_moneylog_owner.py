# Generated by Django 4.0.4 on 2022-05-20 23:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_errorlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moneylog',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='money', to='backend.bot'),
        ),
    ]
