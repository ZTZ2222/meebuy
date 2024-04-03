from django.views.generic import TemplateView, FormView, UpdateView, RedirectView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserTypeSelectionForm


# HomeView
class HomeView(TemplateView):
    template_name = 'home.html'


# RegisterView
class RegisterView(FormView):
    form_class = UserRegistrationForm
    template_name = 'register.html'
    success_url = reverse_lazy('select_user_type')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.auth_provider = False
        form.save()
        return super().form_valid(form)


# LoginView
class LoginView(FormView):
    form_class = UserLoginForm
    template_name = 'login.html'
    success_url = reverse_lazy('select_user_type')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user is not None:
            auth_login(self.request, user)
            if user.auth_provider:
                self.success_url = reverse_lazy('/select_user_type')
            else:
                self.success_url = reverse_lazy('/view_profile')
            return super().form_valid(form)
        else:
            form.add_error(None, "Неверный email или пароль")
            return self.form_invalid(form)


# SelectUserTypeView
class SelectUserTypeView(FormView):
    form_class = UserTypeSelectionForm
    template_name = 'select_user_type.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        if self.request.user.auth_provider:
            self.success_url = reverse_lazy('view_profile')
        return super().form_valid(form)


# LogoutView
class LogoutView(RedirectView):
    url = '/'

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


# ViewProfile
class ViewProfile(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    template_name = 'profile.html'
    success_url = reverse_lazy('view_profile')

    def get_object(self):
        return self.request.user
