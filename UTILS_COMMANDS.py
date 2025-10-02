"""
$ python manage.py migrate              (Aplicar migrações)
$ python manage.py makemigrations       (Criar migrações)
$ python manage.py createsuperuser      (Criar usuário administrador)
$ python manage.py runserver            (Iniciar servidor)
$ python manage.py shell                (Acessar shell do Django)

adminTEST
# Para criar um usuário comum:
    $ python manage.py shell
    >>> from django.contrib.auth import get_user_model
    >>> from django.contrib.auth.models import Group
    >>> User = get_user_model()
    >>> user = User.objects.create_user('vandersonUser', 'vanderson.user@hotmail.com', 'user')
    # Adicionar grupo ao usuário
    >>> admin_group, created = Group.objects.get_or_create(name='Admin')
    >>> user.groups.add(admin_group)
"""