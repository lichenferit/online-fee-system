from django import forms

class ClerkEmailForm(forms.Form):
    email = forms.EmailField(label="Registered Email")

class ClerkOTPForm(forms.Form):
    otp_code = forms.CharField(max_length=6, label="Enter OTP")

class ClerkPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
