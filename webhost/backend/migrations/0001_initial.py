# Generated by Django 4.0.4 on 2022-05-28 23:21

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("token", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=False)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("disabled", "disabled"),
                            ("collecter", "collecter"),
                            ("bumper", "bumper"),
                            ("collecter_and_bumper", "collecter_and_bumper"),
                        ],
                        default="disabled",
                        max_length=100,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TaskSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("next_collect_task", models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ("next_work_task", models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ("next_crime_task", models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                (
                    "bot",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="task_schedule", to="backend.bot"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MoneyLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.IntegerField(default=0)),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("comment", models.TextField(blank=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="money_log", to="backend.bot"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ErrorLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("comment", models.TextField()),
                ("body", models.TextField(blank=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="errors", to="backend.bot"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Balance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cash_balance", models.IntegerField(default=0)),
                ("bank_balance", models.IntegerField(default=0)),
                ("work_earned", models.IntegerField(default=0)),
                ("text_earned", models.IntegerField(default=0)),
                ("collect_earned", models.IntegerField(default=0)),
                ("crime_earned", models.IntegerField(default=0)),
                ("crime_loss", models.IntegerField(default=0)),
                ("initialized", models.BooleanField(default=False)),
                (
                    "bot",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="balance", to="backend.bot"
                    ),
                ),
            ],
        ),
    ]
