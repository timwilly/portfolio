# Spécifie le conteneur de base dans lequel l'image sera crée. Nom:tag
FROM python:3.10.6-slim

# Créer un utilisateur nommé 'portfolio'
RUN useradd portfolio

# L'endroit où l'application sera installée
WORKDIR /home/portfolio

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY portfolio.py config.py boot.sh ./
RUN chmod +x boot.sh

# Environnement de variable pour utilisé les commandes Flask
ENV FLASK_APP=portfolio.py
# On définit l'utilisateur 'portfolio' au lieu de root (qui est par défaut)
RUN chown -R portfolio:portfolio ./
USER portfolio

# Le port utilisé...
EXPOSE 5000
# La commande à être exécuté quand le container est démarré
ENTRYPOINT ["./boot.sh"]
