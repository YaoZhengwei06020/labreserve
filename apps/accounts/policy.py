from django.core.exceptions import PermissionDenied


def is_admin(actor):
    return actor.groups.filter(name="ADMIN").exists()


def require_actor(actor, admin=False):
    if not actor.is_authenticated or not actor.is_active:
        raise PermissionDenied
    if admin and not is_admin(actor):
        raise PermissionDenied
