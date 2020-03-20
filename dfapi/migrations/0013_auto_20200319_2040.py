# Generated by Django 3.0.2 on 2020-03-20 02:40

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dfapi', '0012_auto_20200318_1118'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.AlterModelOptions(
            name='face',
            options={},
        ),
        migrations.RemoveField(
            model_name='subject',
            name='task',
        ),
        migrations.AddField(
            model_name='face',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='faces', to='dfapi.Task'),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_type',
            field=models.CharField(choices=[('video_detect_faces', 'video_detect_faces'), ('video_hunt_faces', 'video_hunt_faces'), ('video_detect_person', 'video_detect_person'), ('video_hunt_person', 'video_hunt_person'), ('predict_genderage', 'predict_genderage'), ('face_clustering', 'face_clustering')], default='video_detect_faces', max_length=64),
        ),
        migrations.CreateModel(
            name='PersonBody',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='faces/')),
                ('box_bytes', models.BinaryField(blank=True, null=True)),
                ('embeddings_bytes', models.BinaryField(blank=True, null=True)),
                ('size_bytes', models.IntegerField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('frame', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_bodies', to='dfapi.Frame')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_bodies', to='dfapi.Subject')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_bodies', to='dfapi.Task')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='task',
            name='tags',
            field=models.ManyToManyField(related_name='tasks', to='dfapi.TaskTag'),
        ),
    ]