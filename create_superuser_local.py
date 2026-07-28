import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'Teddy'
email = 'techbyoraimo@gmail.com'
password = 'Kingofvibez@006'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"? Superuser '{username}' created successfully!")
    print(f"?? Email: {email}")
else:
    print(f"?? Superuser '{username}' already exists.")
