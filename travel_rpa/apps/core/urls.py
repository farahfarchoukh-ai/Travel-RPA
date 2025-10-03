from django.urls import path
from . import views

urlpatterns = [
    path('ingest', views.ingest_email, name='ingest_email'),
    path('simulate-issuance', views.simulate_issuance, name='simulate_issuance'),
]
