from django.urls import path
from my_app.views import second_view, Hi_view, main_chek, login, signup, password,register_view,profile_view
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from my_app import views
from .views import main_chek
urlpatterns = [
    path('', login, name='Login'),
    path('signup/', signup ,name= 'Sign Up'),
    path('newpassword/', password, name='second_page'),
    path('profile/', profile_view, name='Profil'),
    path('register/', register_view, name='register'),
    path('second/', second_view, name='second_page'),
    path('Conculator/', Hi_view,name= 'Hisob'),
    path('soatlar/', main_chek ,name= 'Ish varaqasi'),
    path('ishchi/<str:tabel_id>/', main_chek, name='Ishchi varaqasi'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)