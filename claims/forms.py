from django import forms
from django.conf import settings
from .models import Claim


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['description', 'proof_image']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 5,
                'placeholder': 'Explain precisely why this belongs to you: unique scratches, wallpaper details, serial number, pouch contents, brand specifics...'
            }),
            'proof_image': forms.ClearableFileInput(attrs={'class': 'form-file-input', 'accept': 'image/*'}),
        }

    def clean_proof_image(self):
        image = self.cleaned_data.get('proof_image')
        if image and hasattr(image, 'size'):
            max_size_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 5)
            if image.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"Proof file size cannot exceed {max_size_mb} MB.")
        return image


class OTPVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-input text-center tracking-widest text-2xl font-mono',
            'placeholder': '123456',
            'autocomplete': 'off',
            'maxlength': '6',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Optional handoff notes (e.g. Verified with Student ID card)'
        })
    )
