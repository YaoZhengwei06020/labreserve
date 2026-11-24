from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import LoginForm


class LabLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse("equipment:list")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")
