from django import forms

from apps.equipment.models import Equipment

from .policy import reservation_rule_limits


class EquipmentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.code} · {obj.name}（{obj.get_status_display()}）"


class ReservationForm(forms.Form):
    """Collect reservation input; ownership always comes from the request user."""

    equipment = EquipmentChoiceField(
        label="设备",
        queryset=Equipment.objects.order_by("code"),
        empty_label="请选择设备",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    start = forms.DateTimeField(
        label="开始时间",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"],
        widget=forms.DateTimeInput(
            attrs={"class": "form-control", "type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    end = forms.DateTimeField(
        label="结束时间",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"],
        widget=forms.DateTimeInput(
            attrs={"class": "form-control", "type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        limits = reservation_rule_limits()
        self.fields["start"].help_text = (
            f"预约时长为 {limits['min_minutes']} 分钟至 {limits['max_minutes']} 分钟，"
            f"最多提前 {limits['advance_days']} 天；这些候选规则仍待团队批准。"
        )
