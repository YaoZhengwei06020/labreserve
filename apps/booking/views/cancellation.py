from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import EquipmentSlot
from ..policy import RuleViolation
from ..services import cancel_slot


@login_required
@require_POST
def cancel_reservation(request, slot_id):
    """Cancel the current user's reservation through the shared transaction service."""
    try:
        slot = cancel_slot(actor=request.user, slot_id=slot_id)
    except EquipmentSlot.DoesNotExist as exc:
        raise Http404("预约不存在") from exc
    except PermissionDenied:
        # Do not disclose the equipment, owner, or state of somebody else's slot.
        return render(
            request,
            "booking/cancellation_result.html",
            {"heading": "无法取消预约", "message": "你无权取消该预约。"},
            status=403,
        )
    except RuleViolation as exc:
        return render(
            request,
            "booking/cancellation_result.html",
            {"heading": "无法取消预约", "message": str(exc)},
            status=400,
        )

    messages.success(request, "预约已取消。")
    return HttpResponseRedirect(
        reverse("booking:reservation-detail", kwargs={"slot_id": slot.pk}),
        status=303,
    )
