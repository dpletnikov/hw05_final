# Generated by Django 2.2.16 on 2022-03-04 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220303_1919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/media/', verbose_name='Картинка'),
        ),
    ]