from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.policy import is_admin, require_actor

from .forms import EquipmentForm
from .models import Equipment


@login_required(login_url="accounts:login")
def equipment_list(request):
    require_actor(request.user)
    return render(
        request,
        "equipment/list.html",
        {
            "equipment_list": Equipment.objects.order_by("code"),
            "can_manage": is_admin(request.user),
        },
    )


@login_required(login_url="accounts:login")
def equipment_detail(request, code):
    require_actor(request.user)
    equipment = get_object_or_404(Equipment, code=code)
    return render(
        request,
        "equipment/detail.html",
        {"equipment": equipment, "can_manage": is_admin(request.user)},
    )


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def equipment_create(request):
    require_actor(request.user, admin=True)
    form = EquipmentForm((request.POST if request.method == "POST" else None))
    if request.method == "POST" and form.is_valid():
        equipment = form.save()
        messages.success(request, f"设备 {equipment.code} 已新增。")
        return redirect("equipment:detail", code=equipment.code)
    return render(
        request,
        "equipment/form.html",
        {"form": form, "page_title": "新增设备", "submit_label": "创建设备"},
    )


@login_required(login_url="accounts:login")
@require_http_methods(["GET", "POST"])
def equipment_edit(request, code):
    require_actor(request.user, admin=True)
    equipment = get_object_or_404(Equipment, code=code)
    form = EquipmentForm((request.POST if request.method == "POST" else None), instance=equipment)
    if request.method == "POST" and form.is_valid():
        equipment = form.save()
        messages.success(request, f"设备 {equipment.code} 已更新。")
        return redirect("equipment:detail", code=equipment.code)
    return render(
        request,
        "equipment/form.html",
        {
            "form": form,
            "equipment": equipment,
            "page_title": f"编辑设备 {equipment.code}",
            "submit_label": "保存修改",
        },
    )
