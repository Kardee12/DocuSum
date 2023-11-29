# Generated by Django 4.2.6 on 2023-11-24 04:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sumApp", "0003_chatdata_isai"),
    ]

    operations = [
        migrations.CreateModel(
            name = "Document",
            fields = [
                (
                    "id",
                    models.BigAutoField(
                        auto_created = True,
                        primary_key = True,
                        serialize = False,
                        verbose_name = "ID",
                    ),
                ),
                ("file", models.FileField(upload_to = "documents/")),
            ],
        ),
    ]
