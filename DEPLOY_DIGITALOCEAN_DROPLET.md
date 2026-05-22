# DigitalOcean Droplet Demo Deployment

This is the fastest low-cost deployment path for testing NIITSyllabriq without using the laptop for generation.

Target server:

```text
http://159.89.164.3:5173
```

The droplet deployment uses:

- FastAPI backend on port `8000`
- React/nginx frontend on port `5173`
- Postgres container
- Groq for LLM generation
- Lightweight training mode by default

## 1. SSH Into The Droplet

From your laptop:

```bash
ssh root@159.89.164.3
```

## 2. Install Docker

Run on the droplet:

```bash
apt update
apt install -y ca-certificates curl git ufw
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}) stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 3. Open Firewall Ports

Run on the droplet:

```bash
ufw allow OpenSSH
ufw allow 5173/tcp
ufw allow 8000/tcp
ufw --force enable
```

## 4. Get The Code

Run on the droplet:

```bash
git clone https://github.com/SandeepRDiddi/NIITSyllabriq.git
cd NIITSyllabriq
```

If the repository is private, use a GitHub token or SSH deploy key.

## 5. Create Server Env

Run on the droplet:

```bash
cp .env.droplet.example .env
nano .env
```

Update these values:

```env
GROQ_API_KEY=<your-groq-api-key>
POSTGRES_PASSWORD=<new-password>
DATABASE_URL=postgresql+psycopg://niit:<new-password>@postgres:5432/niit_design_automation
JWT_SECRET_KEY=<long-random-secret>
```

Keep these demo-safe settings:

```env
LLM_PROVIDER=groq
TRAINING_USE_LLM_NORMALIZATION=false
TRAINING_EMBED_ON_UPLOAD=false
ALLOWED_ORIGINS=http://159.89.164.3:5173
VITE_API_BASE_URL=http://159.89.164.3:8000
```

## 6. Start The App

Run on the droplet:

```bash
docker compose -f docker-compose.do.yml up --build -d
```

Check status:

```bash
docker compose -f docker-compose.do.yml ps
docker compose -f docker-compose.do.yml logs -f backend
```

## 7. Test

Open:

- UI: http://159.89.164.3:5173
- API docs: http://159.89.164.3:8000/docs
- Health: http://159.89.164.3:8000/health

Default login:

```text
admin@niit.com / Admin@123
```

## Useful Commands

Restart:

```bash
docker compose -f docker-compose.do.yml restart
```

Rebuild after pulling code:

```bash
git pull
docker compose -f docker-compose.do.yml up --build -d
```

Stop:

```bash
docker compose -f docker-compose.do.yml down
```

View logs:

```bash
docker compose -f docker-compose.do.yml logs -f
```

## Notes

- This is a demo/test deployment, not final SaaS hardening.
- For production, put the app behind HTTPS and move uploaded files to object storage.
- Do not commit `.env`.
