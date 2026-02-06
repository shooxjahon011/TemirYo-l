from django.contrib import admin
from django.contrib import admin
from django.contrib import admin
from django.contrib import admin
from .models import UserProfile

admin.site.register(UserProfile)
from django.contrib import admin
from .models import IshHaqi


@admin.register(IshHaqi)
class IshHaqiAdmin(admin.ModelAdmin):
        list_display = ('tabel_raqam', 'user', 'oklad', 'ishlangan_soat')
        search_fields = ('tabel_raqam', 'user__username')  # Tabel yoki ism bo'yicha qidirish



