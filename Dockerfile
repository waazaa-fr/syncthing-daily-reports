FROM python:3.9-slim

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



RUN pip install requests python-dateutil schedule
COPY ./root /

VOLUME ["/config", "/logs"]
WORKDIR /app
CMD ["python", "syncthing_folders.py"]