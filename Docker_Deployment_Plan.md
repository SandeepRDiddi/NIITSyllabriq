# Docker Deployment Guide

## STEP 1 — Rent a Server

Go to DigitalOcean, create an account, and rent a server.

---

## STEP 2 — Install Docker on the Server

Log into the server and install Docker.

Once Docker is installed, the server can run Docker containers.

---

## STEP 3 — Set Up the Firewall

Only allow web traffic in and block everything else.

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## STEP 4 — Upload Code and Start Docker

### Actions
- Copy the code to the server using `git clone`
- Create a `.env.prod` file with passwords and settings
- Run:

```bash
docker compose up -d
```

Docker reads the `docker-compose.yml` file and automatically starts two containers:

### Container 1: PostgreSQL
The database where all customer data is stored.

### Container 2: FastAPI
The backend API that processes requests and business logic.

Both containers start, connect to each other, and database tables are created automatically.

---

## STEP 5 — Add NGINX

NGINX routes incoming customer requests.

### API Requests

```text
https://app.yourdomain.com/api/
        ↓
      FastAPI
```

### Frontend Requests

```text
https://app.yourdomain.com/
        ↓
     Frontend
```

---

## STEP 6 — Set Up Backup

Configure automated backups.

If something goes wrong — server crash, accidental deletion, or system failure — the system can be restored from the latest backup.

Maximum expected data loss: 24 hours.

---

## STEP 7 — Build the Electron Installer

### Update Backend URL

In `desktop/main.js`, change:

```javascript
localhost:5173
```

to:

```javascript
https://app.domain.com
```

### Build Installer

Run:

```bash
npm run package
```

This generates:

```text
NIIT Design Automation Setup.exe
```

---

## STEP 8 — Create the Customer Account

Use the admin panel to:
- Register the customer
- Set a temporary password
- Share login credentials with the customer

---

## STEP 9 — Hand Over to Customer

### Send the Customer
1. The `.exe` installer file
2. Their email/username
3. Their temporary password

### Customer Steps
1. Double-click the `.exe` installer
2. Install like a normal Windows application
3. Open the application
4. Log in using provided credentials
5. Start using the product

---

# Infrastructure Ownership

We own and control:
- The server
- The database
- The application code
- The AI services

The customer only accesses the application through authenticated login credentials and does not have access to the infrastructure.