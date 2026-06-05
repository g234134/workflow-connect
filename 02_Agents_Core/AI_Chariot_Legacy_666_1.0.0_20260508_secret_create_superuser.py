from django.contrib.auth.models import User
from django.db.utils import IntegrityError


if __name__ == '__main__':
    try:
        User.objects.create_superuser('hobs', 'hobs+aichat.admin@totalgood.com', 'grat3ful4aichat')
    except IntegrityError:
        print('Superuser "hobs" already available.')
