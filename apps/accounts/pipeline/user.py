def confirm_email(user, *args, **kwargs):
    if hasattr(user, 'email_confirmed'):
        user.email_confirmed = True
