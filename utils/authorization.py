from configs import admin


def authorization_check(user_id):
    return user_id in admin
