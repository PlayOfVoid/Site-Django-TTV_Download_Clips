from django import forms

class TwitchClipForm(forms.Form):
    clip_url = forms.URLField(label="Twitch Clip URL")
    quality = forms.ChoiceField(
        label="Quality",
        choices=[
            ("best", "Best"),
            ("720p60", "720p60"),
            ("720p", "720p"),
            ("480p", "480p"),
            ("360p", "360p"),
            ("worst", "Worst"),
            ("source", "Source"),
        ],
        initial="best",
    )