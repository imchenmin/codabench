from django.conf.urls import url
from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    url(r'^signup', views.sign_up, name="signup"),
    path('resend_activation/', views.resend_activation, name='resend_activation'),
    path('login/', views.log_in, name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
            success_url=reverse_lazy('accounts:password_change_done')
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ),
        name='password_change_done'
    ),
    path('user/<slug:username>/account/', views.UserAccountView.as_view(), name="user_account"),
    path('delete/<uidb64>/<token>', views.delete, name='delete'),
]
