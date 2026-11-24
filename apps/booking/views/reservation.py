from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.policy import is_admin
from apps.equipment.models import Equipment

from ..forms import ReservationForm
from ..models import EquipmentSlot
from ..policy import RuleViolation, SlotConflict
from ..services import create_slot


@login_required
@require_GET
def create_reservation(request):
    initial = {}
    equipment_id = request.GET.get("equipment")
    if equipment_id and equipment_id.isdecimal():
        initial["equipment"] = equipment_id
    return render(request, "booking/reservation_form.html", {"form": ReservationForm(initial=initial)})


@login_required
@require_POST
def create_reservation_submit(request):
    # A well-formed but unknown equipment id is a missing resource, not a form error.
    equipment_id = request.POST.get("equipment")
    try:
        equipment_pk = int(equipment_id) if equipment_id is not None else None
    except ValueError:
        equipment_pk = None
    if equipment_pk is not None:
        get_object_or_404(Equipment, pk=equipment_pk)

    form = ReservationForm(request.POST)
    if not form.is_valid():
        return render(request, "booking/reservation_form.html", {"form": form}, status=400)

    try:
        slot = create_slot(
            actor=request.user,
            equipment_id=form.cleaned_data["equipment"].pk,
            kind=EquipmentSlot.Kind.RESERVATION,
            start=form.cleaned_data["start"],
            end=form.cleaned_data["end"],
        )
    except SlotConflict as exc:
        form.add_error(None, str(exc))
        return render(request, "booking/reservation_form.html", {"form": form}, status=409)
    except RuleViolation as exc:
        form.add_error(None, str(exc))
        return render(request, "booking/reservation_form.html", {"form": form}, status=400)
    except Equipment.DoesNotExist as exc:
        raise Http404("设备不存在") from exc

    return HttpResponseRedirect(
        reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk}),
        status=303,
    )


@login_required
@require_GET
def reservation_detail(request, slot_id):
    slot = get_object_or_404(
        EquipmentSlot.objects.select_related("equipment", "user"),
        pk=slot_id,
        kind=EquipmentSlot.Kind.RESERVATION,
    )
    if slot.user_id != request.user.pk and not is_admin(request.user):
        raise PermissionDenied
    return render(request, "booking/reservation_detail.html", {"slot": slot})
