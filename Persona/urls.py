from django.urls import path
from Persona import views

urlpatterns = [
    path('cuidador/', views.vwCuidador.as_view()),
    path('autenticacion/', views.vwAutenticacion.as_view()),
    path('custodiado/', views.vwCustodiado.as_view())
]