def staff_with(permission):
    def check(user):
        return user.is_authenticated and user.is_staff and (user.is_superuser or user.has_perm(permission))
    return check
