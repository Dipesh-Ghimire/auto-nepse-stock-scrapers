from django import forms
import hashlib
from .models import TMSAccount
from django.core.exceptions import ValidationError

class TMSLoginForm(forms.Form):
    broker_number = forms.IntegerField(label="Broker Number", min_value=1)
    username = forms.CharField(label="Username", required=True)
    password = forms.CharField(widget=forms.PasswordInput(), label="Password", required=True)


class TMSAccountForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput)
    make_primary = forms.BooleanField(
        required=False,
        label="Set as primary account",
        help_text="This will be your default TMS account"
    )
    class Meta:
        model = TMSAccount
        fields = ['broker_number', 'username', 'password', 'make_primary']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.initial['username'] = self.instance.username
            self.initial['password'] = self.instance.password
            self.initial['make_primary'] = self.instance.is_primary
            
        # Hide make_primary checkbox if this is the only account
        if self.user and TMSAccount.objects.filter(user=self.user).count() <= 1:
            self.fields['make_primary'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        broker_number = cleaned_data.get('broker_number')
        
        if username and broker_number:
            # Calculate the hash to check against the database
            username_hash = hashlib.sha256(username.encode()).hexdigest()
            
            # Check for existing records with same broker_number and username_hash
            queryset = TMSAccount.objects.filter(
                broker_number=broker_number,
                username_hash=username_hash
            )
            
            # If editing, exclude current instance
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
                
            if queryset.exists():
                raise ValidationError(
                    'A TMS account with this broker number and username already exists'
                )
                
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if not instance.pk and self.user:
            instance.user = self.user
        
        # Handle primary account selection
        make_primary = self.cleaned_data.get('make_primary', False)
        if make_primary:
            # Clear primary flag from other accounts
            TMSAccount.objects.filter(user=instance.user).update(is_primary=False)
            instance.is_primary = True
        # These setters will handle both encryption and hashing
        instance.username = self.cleaned_data['username']
        instance.password = self.cleaned_data['password']
        
        
        if commit:
            instance.save()
        return instance