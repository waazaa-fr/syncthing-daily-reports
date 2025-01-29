FROM python:3.9-slim

# Variables d'environnement
ENV SYNCTHING_URL           = ""
ENV SYNCTHING_API_KEY       = ""
ENV SYNCTHING_DAYS_INACTIVE = 30

ENV SMTP_ENABLE             = "false"
ENV SMTP_SERVER             = ""
ENV SMTP_PORT               = 587
ENV SMTP_USERNAME           = ""
ENV SMTP_PASSWORD           = ""
ENV SMTP_SENDER             = ""
ENV SMTP_RECEIVER           = ""

ENV GOTIFY_ENABLE           = "false"
ENV GOTIFY_URL              = ""
ENV GOTIFY_TOKEN            = ""

ENV DISCORD_ENABLE          = "false"
ENV DISCORD_WEBHOOK         = ""


# Paquets essentiels
RUN pip install --upgrade pip && \
    pip install requests python-dateutil schedule

# Déplacement de la source dans l'image
COPY ./root /


VOLUME ["/config", "/logs"]
WORKDIR /app
CMD ["python", "app.py"]