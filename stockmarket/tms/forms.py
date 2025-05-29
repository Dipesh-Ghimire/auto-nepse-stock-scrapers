from django import forms

class TMSLoginForm(forms.Form):
    broker_number = forms.IntegerField(label="Broker Number", min_value=1)
    username = forms.CharField(label="Username", required=True)
    password = forms.CharField(widget=forms.PasswordInput(), label="Password", required=True)