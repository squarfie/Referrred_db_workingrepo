from apps.home.permissions import role_flags


def user_access(request):
    return {
        "user_access": role_flags(request.user),
    }

