# Analytic-Eyes
uma api que monitorar outras ETLs

Criar um novo app Django
    docker compose exec backend python manage.py startapp nome_do_app
    Exemplo:
    docker compose exec backend python manage.py startapp pipelines

Criar migrações (makemigrations)
    docker compose exec backend python manage.py makemigrations

Se quiser gerar só para um app específico:
    docker compose exec backend python manage.py makemigrations pipelines

Aplicar migrações no banco (migrate)
    docker compose exec backend python manage.py migrate

Criar superusuário
    docker compose exec backend python manage.py createsuperuser

Abrir shell do Django
    docker compose exec backend python manage.py shell

Rodar testes
    docker compose exec backend python manage.py test

Se você ainda não fez docker compose up, use:

docker compose run backend python manage.py ...

docker compose up
