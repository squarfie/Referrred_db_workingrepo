# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import *
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})


# Forgot Password View (search by username or email)
def forgot_password_view(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get("username_or_email")
            try:
                user = User.objects.get(username=username_or_email)  # Try by username
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=username_or_email)  # Try by email
                except User.DoesNotExist:
                    messages.error(request, "User not found.")
                    return render(request, "accounts/forgot_password.html", {"form": form})

            request.session['reset_user_id'] = user.id
            return redirect("reset_password")  # Ensure URL name matches
    else:
        form = ForgotPasswordForm()

    return render(request, "accounts/forgot_password.html", {"form": form})


# Reset Password View
def reset_password_view(request):
    user_id = request.session.get("reset_user_id")
    
    if not user_id:
        return redirect("forgot_password")  # Ensure URL name matches

    try:
        user = User.objects.get(id=user_id)
        messages.success(request, "Please enter a new password.")
    except User.DoesNotExist:
        messages.error(request, "User not found, please try again.")
        return redirect("forgot_password")

    form = CustomPasswordResetForm()

    if request.method == "POST":
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data["password1"]
            password2 = form.cleaned_data["password2"]

            if password1 == password2:
                try:
                    validate_password(password1, user)  # Validate password strength
                    user.password = make_password(password1)
                    user.save()
                    del request.session["reset_user_id"]
                    messages.success(request, "Password reset successful")
                    return redirect("login")
                except ValidationError as e:
                    messages.error(request, f"Password validation error: {', '.join(e.messages)}")
            else:
                messages.error(request, "Passwords do not match.")
    
    return render(request, "accounts/reset_password.html", {"form": form})

# Logging out
def logout_view(request):
    logout(request)  # Logs out the user
    return redirect("login")
