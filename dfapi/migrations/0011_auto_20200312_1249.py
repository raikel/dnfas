# Generated by Django 3.0.2 on 2020-03-12 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dfapi', '0010_auto_20200311_1255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='face',
            name='pred_sex',
            field=models.CharField(blank=True, choices=[('man', 'man'), ('woman', 'woman')], default='', max_length=16),
        ),
    ]