from django import forms
from django.conf import settings
from .models import Item, Category, CampusLocation


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'item_type',
            'title',
            'category',
            'location',
            'specific_spot',
            'incident_date',
            'description',
            'identifying_details',
            'image',
            'holding_location',
        ]
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Matte Black Hydro Flask Water Bottle'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'specific_spot': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 2nd floor, silent study cubicle #14'}),
            'incident_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Provide clear physical visual details (color, brand, visible stickers)...'}),
            'identifying_details': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Optional secret verification details (lockscreen picture, serial #, private marks). Kept hidden from the public to verify legitimate claims!'}),
            'holding_location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Kept with Finder / Handed to Security Desk Room 102'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-file-input', 'accept': 'image/*'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            max_size_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 5)
            if image.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"Image file size cannot exceed {max_size_mb} MB.")
        return image
