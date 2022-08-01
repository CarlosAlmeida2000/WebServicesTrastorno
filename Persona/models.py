from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.db import transaction
from fernet_fields import EncryptedTextField
from django.db import IntegrityError
from file import File
import os

# Create your models here.
class Roles(models.Model):
    nombre = models.CharField(max_length = 10)

class Personas(models.Model):
    nombres = models.CharField(max_length = 40)
    apellidos = models.CharField(max_length = 40)
    cedula = models.CharField(max_length = 10, unique = True)
    fecha_nacimiento = models.DateField()
    foto_perfil = models.ImageField(upload_to = 'Perfiles', null = True, blank = True)

    def guardar(self, json_data, rol):
        punto_guardado = transaction.savepoint()
        try:
            if 'persona__nombres' in json_data:
                self.nombres = json_data['persona__nombres']
            if 'persona__apellidos' in json_data:
                self.apellidos = json_data['persona__apellidos']
            if 'persona__cedula' in json_data:
                self.cedula_ruc = json_data['persona__cedula']
            if 'persona__fecha_nacimiento' in json_data:
                self.fecha_nacimiento = json_data['persona__fecha_nacimiento']
            self.save()
            if rol != '' and len(RolesPersonas.objects.filter(persona__cedula = json_data['persona__cedula']).select_related('rol').filter(rol__nombre = rol)) == 0:
                rol_persona = RolesPersonas()
                rol_persona.persona = self
                rol_persona.rol = (Roles.objects.get(nombre = rol))
                rol_persona.save()                    
            if 'persona__foto_perfil' in json_data and json_data['persona__foto_perfil'] != '':
                ruta_img_borrar = ''
                if(str(self.foto_perfil) != ''):
                    ruta_img_borrar = self.foto_perfil.url[1:]
                file = File()
                file.base64 = json_data['persona__foto_perfil']
                file.nombre_file = 'persona_' + str(self.id)
                self.foto_perfil = file.get_file()
                self.save()
                if(ruta_img_borrar != ''):
                    os.remove(ruta_img_borrar)
            return 'si', self
        except IntegrityError:
            transaction.savepoint_rollback(punto_guardado)
            return 'cédula repetida', None
        except Exception as e: 
            transaction.savepoint_rollback(punto_guardado)
            return 'error', None
    
class RolesPersonas(models.Model):
    persona = models.ForeignKey('Persona.Personas', on_delete = models.PROTECT, related_name = 'roles_persona')
    rol = models.ForeignKey('Persona.Roles', on_delete = models.PROTECT)
    

class Usuarios(models.Model):
    nom_usuario = models.CharField(max_length = 20, unique = True)
    clave = EncryptedTextField()
    persona = models.OneToOneField('Persona.Personas', on_delete = models.PROTECT, unique = True)

    @staticmethod
    def obtener_datos(request):
        try:
            if 'id' in request.GET:
                usuarios = Usuarios.objects.filter(pk = request.GET['id'])   
            elif 'persona__cedula' in request.GET:
                usuarios = Usuarios.objects.filter(persona__cedula__contains = request.GET['persona__cedula'])   
            elif 'nombres_apellidos' in request.GET:
                usuarios = (Usuarios.objects.all().select_related('persona')).annotate(nombres_completos = Concat('persona__nombres', Value(' '), 'persona__apellidos'))
                usuarios = usuarios.filter(nombres_completos__contains = request.GET['nombres_apellidos'])
            else:
                usuarios = Usuarios.objects.all()
            usuarios = usuarios.order_by('nom_usuario').select_related('persona').values('id', 'nom_usuario', 
                'persona_id','persona__nombres', 'persona__apellidos', 'persona__cedula', 'persona__fecha_nacimiento', 'persona__foto_perfil')
            file = File()
            for u in range(len(usuarios)):
                if(usuarios[u]['persona__foto_perfil'] != ''):
                    file.ruta = usuarios[u]['persona__foto_perfil']
                    usuarios[u]['persona__foto_perfil'] = file.get_base64()
            return list(usuarios)
        except Exception as e: 
            return 'error'

    def guardar(self, json_data):
        punto_guardado = transaction.savepoint()
        try:
            persona_editar = Personas.objects.get(cedula_ruc = json_data['persona__cedula'])
            persona_guardada, self.persona = persona_editar.guardar(json_data, 'Cuidador')
            if(persona_guardada == 'si'):
                if 'nom_usuario' in json_data:
                    self.nom_usuario = json_data['nom_usuario']
                if 'clave' in json_data:
                    self.clave = json_data['clave']
                self.save()
                return 'guardado'
            else:
                return persona_guardada
        except IntegrityError:
            transaction.savepoint_rollback(punto_guardado)
            return 'usuario repetido'
        except Exception as e: 
            transaction.savepoint_rollback(punto_guardado)
            return 'error'

    @staticmethod
    def login(json_data):
        try:
            usuario = Usuarios.objects.get(nom_usuario = json_data['usuario'])
            if(usuario.clave == json_data['clave']):
                file = File()
                roles = RolesPersonas.objects.filter(persona_id = usuario.persona.id).select_related('rol')
                base64 = ''
                if(usuario.persona.foto_perfil != ''):
                    file.ruta = usuario.persona.foto_perfil
                    base64 = file.get_base64()
                json_usuario = {
                        'id': usuario.pk,
                        'nom_usuario': usuario.nom_usuario,
                        "foto_perfil": base64,
                        "persona_id": usuario.persona.pk,
                        "persona__nombres": usuario.persona.nombres,
                        "persona__apellidos": usuario.persona.apellidos,
                        "persona__cedula": usuario.persona.cedula,
                        "persona__fecha_nacimiento": usuario.persona.fecha_nacimiento,
                        'roles': {roles.values('rol__nombre')}
                        }
                return json_usuario
            else:   
                return 'credenciales incorrectas'
        except Usuarios.DoesNotExist:
            return 'credenciales incorrectas'
        except Exception as e: 
            return 'error'

class Custodiados(models.Model):
    cuidador = models.ForeignKey('Persona.Usuario', on_delete = models.PROTECT)
    custodiado = models.ForeignKey('Persona.Personas', on_delete = models.PROTECT)

    @staticmethod
    def obtener_datos(request):
        try:
            if 'id' in request.GET:
                custodiados = Custodiados.objects.filter(Q(pk = request.GET['id']) & Q(cuidador__pk = request.GET['usuario_id']))   
            elif 'persona__cedula' in request.GET:
                custodiados = Custodiados.objects.filter(Q(custodiado__cedula__contains = request.GET['persona__cedula']) & Q(cuidador__pk = request.GET['usuario_id']))   
            elif 'nombres_apellidos' in request.GET:
                custodiados = (Custodiados.objects.filter(cuidador__pk = request.GET['usuario_id']).select_related('custodiado')).annotate(nombres_completos = Concat('custodiado__nombres', Value(' '), 'custodiado__apellidos'))
                custodiados = custodiados.filter(nombres_completos__contains = request.GET['nombres_apellidos'])
            else:
                custodiados = Custodiados.objects.filter(cuidador__pk = request.GET['usuario_id'])
            custodiados = custodiados.select_related('custodiado').values('id', 
                'custodiado_id','custodiado__nombres', 'custodiado__apellidos', 'custodiado__cedula', 'custodiado__fecha_nacimiento', 'custodiado__foto_perfil')
            file = File()
            for u in range(len(custodiados)):
                if(custodiados[u]['custodiado__foto_perfil'] != ''):
                    file.ruta = custodiados[u]['custodiado__foto_perfil']
                    custodiados[u]['custodiado__foto_perfil'] = file.get_base64()
            return list(custodiados)
        except Exception as e: 
            return 'error'

    def guardar(self, json_data):
        punto_guardado = transaction.savepoint()
        try:
            persona_editar = Personas.objects.get(cedula_ruc = json_data['persona__cedula'])
            persona_guardada, self.persona_custodiada = persona_editar.guardar(json_data, 'Custodiado')
            if(persona_guardada == 'si'):
                self.cuidador = Usuarios.objects.get(pk = json_data['usuario_id'])    
                self.save()
                return 'guardado'
            else:
                return persona_guardada    
        except Exception as e: 
            transaction.savepoint_rollback(punto_guardado)
            return 'error'