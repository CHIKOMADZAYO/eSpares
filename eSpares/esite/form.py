from django import forms
from .models import User



class UserLoginForm(forms.ModelForm):

    class Meta:
        model=User
        fields=(
            "username",
            "password"
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            
        }


    def __init__(self,*args, **kwargs):
        super(UserLoginForm,self).__init__(*args,**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class']='form-control'



class UserRegistrationForm(forms.ModelForm):
    model=User
    fields="__all__"

    def __init__(self,*args, **kwargs):
        super(UserRegistrationForm,self).__init__(*args,**kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class']='form-control'




class ProductForm(forms.Form):
    name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    price = forms.DecimalField(max_digits=10, decimal_places=2)
    image = forms.ImageField()



