from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import ContactMessage, CustomerProfile, Device, RepairRequest, RepairService


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class RepairPhotoListField(forms.FileField):
    widget = MultipleImageInput(attrs={"multiple": True})

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        if len(files) > 3:
            raise forms.ValidationError("Upload up to 3 photos.")
        image_field = forms.ImageField()
        cleaned = []
        for upload in files:
            image = image_field.clean(upload)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Each image must be 5 MB or smaller.")
            cleaned.append(image)
        return cleaned
class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class']='form-control'



class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ("username", "email")

    def __init__(self,*args, **kwargs):
        super(UserRegistrationForm,self).__init__(*args,**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class']='form-control'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The passwords do not match.")
        return password2

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        candidate = get_user_model()(
            username=self.cleaned_data.get("username", ""),
            email=self.cleaned_data.get("email", ""),
        )
        try:
            validate_password(password, user=candidate)
        except forms.ValidationError as error:
            raise error
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user




class ProductForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    price = forms.DecimalField(max_digits=10, decimal_places=2)
    image = forms.ImageField()


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = CustomerProfile
        fields = ("phone", "address")

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in ("first_name", "last_name", "email"):
            self.fields[field].initial = getattr(user, field)

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        users = get_user_model().objects.filter(email__iexact=email).exclude(pk=self.user.pk)
        if users.exists():
            raise forms.ValidationError("This email address is already used by another account.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save(update_fields=["first_name", "last_name", "email"])
            profile.user = self.user
            profile.save()
        return profile


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ("brand", "model_name", "serial_number", "imei", "condition", "notes", "photo")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["brand"].queryset = self.fields["brand"].queryset.filter(
            name__in=["Samsung", "Apple", "TECNO", "Infinix", "OPPO", "vivo", "realme"]
        )

    def clean_imei(self):
        value = self.cleaned_data.get("imei", "").strip()
        if value and (not value.isdigit() or len(value) not in (14, 15, 16)):
            raise forms.ValidationError("Enter a 14, 15 or 16 digit IMEI, or leave it blank.")
        return value


class RepairBookingForm(forms.ModelForm):
    photos = RepairPhotoListField(required=False, label="Photos (up to 3, 5 MB each)")

    class Meta:
        model = RepairRequest
        fields = ("device", "service", "problem", "preferred_date", "fulfillment", "service_address")
        widgets = {
            "problem": forms.Textarea(attrs={"rows": 5}),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, customer, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = Device.objects.filter(customer=customer)
        self.fields["service"].queryset = RepairService.objects.filter(is_active=True)

    def clean_preferred_date(self):
        value = self.cleaned_data["preferred_date"]
        if value < timezone.localdate():
            raise forms.ValidationError("Choose today or a future date.")
        return value

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("fulfillment") == "collection" and not cleaned.get("service_address", "").strip():
            self.add_error("service_address", "Enter the collection address so the team can review your request.")
        return cleaned


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}


class RepairTrackingForm(forms.Form):
    reference = forms.CharField(max_length=32, label="Repair reference")


class ChatMessageForm(forms.Form):
    body = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={"rows": 3}), label="Message")



