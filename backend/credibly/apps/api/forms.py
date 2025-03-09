from django import forms

from .models import BiasedMedia


class MediaDataForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["media"] = forms.ModelChoiceField(queryset=BiasedMedia.objects.all())
