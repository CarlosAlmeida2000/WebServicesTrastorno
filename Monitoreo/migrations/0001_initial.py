# Generated by Django 3.0.8 on 2022-09-02 03:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Persona', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vigilancia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Historial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_hora', models.DateTimeField()),
                ('dia', models.IntegerField()),
                ('imagen_expresion', models.ImageField(blank=True, null=True, upload_to='Expresiones_detectadas')),
                ('expresion_facial', models.CharField(max_length=15)),
                ('custodiado', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historial_custodiado', to='Persona.Custodiados')),
            ],
        ),
    ]
