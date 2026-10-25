# Розгортання FinPulse (Ubuntu)

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin finpulse
sudo mkdir -p /opt/finpulse && sudo chown finpulse:finpulse /opt/finpulse
sudo -u finpulse git clone -b main https://github.com/Bodyaaaaaaaq/finpulse.git /opt/finpulse

cd /opt/finpulse/server
sudo -u finpulse python3.12 -m venv .venv
sudo -u finpulse .venv/bin/pip install -r requirements.txt

sudo -u finpulse cp .env.example .env
sudo -u finpulse nano .env
sudo chmod 600 .env

sudo -u finpulse .venv/bin/alembic upgrade head

sudo cp /opt/finpulse/deploy/finpulse.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now finpulse

systemctl status finpulse
curl http://127.0.0.1:8000/api/health
journalctl -u finpulse -f
```

Міграції не запускаються автоматично при рестарті, їх виконують вручну.