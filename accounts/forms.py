from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from .models import UserProfile


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'student@campus.edu or username',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'id': 'login-password-field',
        })
    )

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        if username_or_email and '@' in username_or_email:
            # Look up username from email
            user_match = User.objects.filter(email__iexact=username_or_email).first()
            if user_match:
                self.cleaned_data['username'] = user_match.username
        return super().clean()


class CampusRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Last Name'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Choose username'})
    )
    email = forms.EmailField(
        required=True,
        label="Campus Email",
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'campus_email@university.edu'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Create secure password',
            'id': 'reg-password-field',
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Confirm your password',
            'id': 'reg-confirm-password-field',
        })
    )
    
    campus_id = forms.CharField(
        max_length=50,
        required=False,
        label="Campus ID (Optional)",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'e.g. STU-88219'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        label="Department (Optional)",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'e.g. Computer Science'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label="Phone Number (Optional)",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': '+1 (555) 000-0000'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        
        allowed_domain = getattr(settings, 'CAMPUS_ALLOWED_EMAIL_DOMAIN', '').strip()
        if allowed_domain:
            if not email.endswith(f"@{allowed_domain}"):
                raise forms.ValidationError(f"Registration is restricted to @{allowed_domain} addresses.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            profile = user.profile
            profile.campus_id = self.cleaned_data.get('campus_id', '')
            profile.department = self.cleaned_data.get('department', '')
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = UserProfile
        fields = ['campus_id', 'department', 'phone_number', 'avatar']
        widgets = {
            'campus_id': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
        }
