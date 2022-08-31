from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Roles)
admin.site.register(Personas)
admin.site.register(RolesPersonas)
admin.site.register(Usuarios)
admin.site.register(Custodiados)