Be informed when your SyncThing synced folders updates are too old perhaps if problem occured on clients.


**docker run**
```bash
docker run -it --rm --name test-syncthing \
    -e SYNCTHING_URL="http://syncthing.url" -e SYNCTHING_API_KEY="gXxxxxxxxxxt" -e SYNCTHING_DAYS_INACTIVE=30 \
    -e SMTP_ENABLE="true" -e SMTP_SERVER="mail.example.com" -e SMTP_PORT=587 -e SMTP_USERNAME="you@example.com" \
    -e SMTP_PASSWORD="P4ssw0rd" -e SMTP_SENDER="you@example.com" -e SMTP_RECEIVER="you@example.com" \
    -e GOTIFY_ENABLE="true" -e GOTIFY_URL="http://gotify.url" -e GOTIFY_TOKEN="Axx.xxxxx" \
    -e DISCORD_ENABLE="true" -e DISCORD_WEBHOOK="https://discordapp.com/api/webhooks/xxx" \
    -v $PWD/config:/config -v $PWD/logs:/logs \
    waazaafr/syncthing-daily-reports:latest
```

**docker compose**
```yml
services:
  pydio:
    image: waazaafr/syncthing-daily-reports:latest
    container_name: syncthing-daily-reports
    hostname: syncthing-daily-reports
    restart: always
    environment:
      - "SYNCTHING_URL=http://syncthing.url"
      - "SYNCTHING_API_KEY=gXxxxxxxxxxt"
      - "SYNCTHING_DAYS_INACTIVE=30"
      - "SMTP_ENABLE=true"
      - "SMTP_SERVER=mail.example.com"
      - "SMTP_PORT=587"
      - "SMTP_USERNAME=you@example.com"
      - "SMTP_PASSWORD=P4ssw0rd"
      - "SMTP_SENDER=you@example.com"
      - "SMTP_RECEIVER=you@example.com"
      - "GOTIFY_ENABLE=true"
      - "GOTIFY_URL=http://gotify.url"
      - "GOTIFY_TOKEN=Axx.xxxxx"
      - "DISCORD_ENABLE=true"
      - "DISCORD_WEBHOOK=https://discordapp.com/api/webhooks/xxx"
    volumes:
      - ./config:/config
      - ./logs:/logs
```

Variables are easy to understand.

You can activate notification through:
- email
- gotify
- discord

The variable SYNCTHING_DAYS_INACTIVE is the number of past days before marking synced folders as inactive.

=======================================================================

Feel free to join me on https://discord.gg/p9xkjEw8ts⁠

If you like this, consider buing me a coffee: https://buymeacoffee.com/waazaa⁠

If you need an UnRAID license follow this link: https://unraid.net/pricing?via=4c3f80⁠