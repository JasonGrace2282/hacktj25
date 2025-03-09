from django import forms

from .models import BiasedMedia


class MediaDataForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["media"] = forms.CharField()

    def clean_media(self):
        media = self.cleaned_data["media"]
        return BiasedMedia.objects.get(url=media)
