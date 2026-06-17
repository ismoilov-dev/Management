# apps/grades/apps.py
"""
Baho app konfiguratsiyasi.
Django uchun zarur sozlamalar.
"""

from django.apps import AppConfig


class GradesConfig(AppConfig):
    """
    Baho app'ning konfiguratsiya sinfi.
    """
    
    # App'ning ichki nomi
    name = 'apps.grades'
    