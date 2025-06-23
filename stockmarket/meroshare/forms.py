from django import forms
from .models import MeroShareAccount
from .capital import CAPITALS

class MeroShareAccountForm(forms.ModelForm):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter Meroshare username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Meroshare password'})
    )
    crn = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter Customer Registration Number'})
    )
    pin = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Enter PIN for Meroshare'})
    )
    dp = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-live-search': 'true',
            'id': 'dp-select'
        }),
        required=True
    )

    class Meta:
        model = MeroShareAccount
        fields = ['alias_name', 'dp', 'username', 'password', 'crn', 'pin', 'auto_ipo_apply']
        
        widgets = {
            'alias_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter NickName'}),
            'auto_ipo_apply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dp'].choices = self.get_dp_choices()
        
        # Set initial values for the custom fields if instance exists
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['crn'].initial = self.instance.crn
            self.fields['pin'].initial = self.instance.pin

    def get_dp_choices(self):
        # Create choices from CAPITALS data
        choices = [('', '---------')]  # Empty/default choice
        for capital in CAPITALS:
            choices.append((capital['code'], f"{capital['code']} - {capital['name']}"))
        return choices
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.username = self.cleaned_data['username']
        instance.password = self.cleaned_data['password']
        instance.crn = self.cleaned_data['crn']
        instance.pin = self.cleaned_data['pin']
        if commit:
            instance.save()
        return instance
