
estou desenvolvendo um software de automação de emissão de notas fiscais para uma empresa que utiliza uma plataforma própria no estilo 'sygecom'. esse software vai receber inputs do usuário (como empresa, valores, tipo de operação, destinatário, entre outros) e realizar ações no sistema. vou fazer a automação utilizando Python com playwright e gostaria de ter uma interface web simples e responsiva, com login e inputs a serem recebidos pela automação, e a inicialização do playwright em um VPS (servidor), talvez atraves de um container docker.

Decidi seguir a seguinte abordagem:

"""
1. Aplicação Web (mais escalável e acessível)

Hospedagem do backend (Python + Playwright).

Painel web (Django/Flask + React/Vue).

O cliente acessa via navegador (PC ou celular).

Cada usuário faz login no seu sistema.

O backend dispara a automação no Playwright e retorna o resultado (ex: PDF da NF).


- HOSPEDAGEM:

VPS tradicional (mais barato)

DigitalOcean, Hetzner, Linode, Contabo

Criar uma VM (Ubuntu).

Instala Docker + Playwright e sobe seu backend.
"""

minha arquitetura inicial está assim:
"""
reciminas-automation/
    server/
        core/
            __init__.py
            asgi.py
            settings.py
            urls.py
            wsgi.py
        invoices_automation/
            migrations/
                __init__.py
            services/
                __init__.py
                invoices_generator.py
            utils/
                __init__.py
                coordinates.py
            __init__.py
            admin.py
            apps.py
            forms.py
            models.py
            tests.py
            urls.py
            views.py
        templates/
        .env
        db.sqlite3
        env.sample
        manage.py
    venv/
    .gitignore
    .pre-commit-config.yaml
    .python-version
    README.md
    requirements.txt
"""

como devo estruturar inicialmente meus arquivos para criar uma página inicial de login?