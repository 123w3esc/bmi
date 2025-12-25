from django.contrib import admin
from django.urls import path
from BMICalc.core import views

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
    path('calculate_bmi/', views.calculate_bmi, name='calculate_bmi'),
    path('track_progress/', views.track_progress, name='track_progress'),
    path('diet/<str:status>/', views.diet_plan, name='diet_plan'),
    path('diet_diabetes/<str:status>/', views.diet_diabetes, name='diet_diabetes'),
    path('diet_bp/<str:status>/', views.diet_bp, name='diet_bp'),
    path('workout/<str:status>/', views.workout_plan, name='workout_plan'),
    path('admin-panel/', views.admin_home, name='admin_home'),
    path('admin-panel/manage-users/', views.manage_users, name='manage_users'),
    path('admin-panel/verify/<int:user_id>/', views.verify_user, name='verify_user'),
    path('admin-panel/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-panel/make-admin/<int:user_id>/', views.make_admin, name='make_admin'),
    path('specialists/', views.specialist_bot, name='specialist_bot'),
    path('download-report/', views.download_report, name='download_report'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),




]

# ✅ Serve static files during development
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])