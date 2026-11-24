from django import forms

from .models import Equipment


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["code", "name", "description", "location"]
        labels = {
            "code": "设备编号",
            "name": "设备名称",
            "description": "设备描述",
            "location": "设备位置",
        }
        error_messages = {
            "code": {"unique": "设备编号已存在，请使用其他编号。"},
        }
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "maxlength": 40}),
            "name": forms.TextInput(attrs={"class": "form-control", "maxlength": 120}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "location": forms.TextInput(attrs={"class": "form-control", "maxlength": 200}),
        }
