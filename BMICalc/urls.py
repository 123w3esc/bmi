from django.contrib import admin
from django.urls import path
from core import views

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('changePass', views.changePass, name='changePass'),
    path('verify', views.verify, name='verify'),
    path('forgetPass', views.forget, name='forgetPass'),
    path('user', views.user_home, name='user'),
    path('logout', views.logout, name='logout'),
]

# ✅ Serve static files during development
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])