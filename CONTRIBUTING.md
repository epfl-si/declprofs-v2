# Contributing

## Prerequisites

- Access to the Keybase team `epfl_declprofs`.
- Access to the two different OpenShift environments (test | prod)

## Setup

Clone the repository:

```bash
git clone git@github.com:epfl-si/declprofs-v2.git
```

## Help

```bash
make help
```

## Build / Run

```bash
make local-build
make local-up
```

For first use (local is up, and replace <your_user-name> by your username):

```bash
make local-django-exec

python manage.py migrate

python manage.py shell
```

and copy paste in the python shell:

```bash
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.get(username="<your_user_name>")

user.is_staff = True
user.has_access = True
user.is_superuser = True
user.save()
```

You'll be superuser. If you want to switch in user mode, juste set and save:

```bash
user.is_superuser = False
user.save()
```

## Tests

Unit tests and integration tests

```bash
make test
```

Coverage

```bash
make coverage        # text report
# or
make coverage-html   # html report
```

## Deploy

Run the declsible script with an environment :

```sh
./ansible/declsible [ --test | --prod ]
```
