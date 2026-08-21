# BIPAGEN 

<p align="center">
  <img src="" alt="logo"/>
</p>

EMU Biological Collections Infrastructure,

## Installation

Install Miniconda if you don't have it:

```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Create the conda environment from `environment.yml` (installs Flask, SQLAlchemy, python-dotenv, and all dependencies) and activate it:

```
conda env create -f environment.yml
conda activate bgen
```

If the environment already exists, update it with:

```
conda env update -f environment.yml
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```
cp .env.example .env
```

The app reads `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_EMAIL` from `.env`. Default admin credentials are `admin` / `admin123`.

Service request emails are sent via SMTP using the following variables:

```
MAIL_TO=<recipient address>
SMTP_HOST=<smtp server>
SMTP_PORT=587
SMTP_USER=<smtp user>
SMTP_PASSWORD=<smtp password>
SMTP_TLS=true
SMTP_SSL=false
```

### Email options (choose one)

#### Option 1 — Brevo (recommended)

1. Sign up at https://www.brevo.com (free tier includes 300 emails/day).
2. In **SMTP & API → SMTP**, copy the **SMTP login** and **SMTP key**.
3. Configure `.env`:

```
MAIL_TO=your-recipient@example.com
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=<your Brevo SMTP login>
SMTP_PASSWORD=<your Brevo SMTP key>
SMTP_TLS=true
SMTP_SSL=false
```

4. Add your sending address (the `MAIL_TO` address) as a verified Sender in Brevo.

#### Option 2 — Gmail App Password

1. Enable **2-Step Verification** at https://myaccount.google.com/security (required for app passwords).
2. Create an **App Password** at https://myaccount.google.com/apppasswords.
3. Configure `.env`:

```
MAIL_TO=your-recipient@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your gmail address>
SMTP_PASSWORD=<16-character app password>
SMTP_TLS=true
SMTP_SSL=false
```

Note: for servers that do not require authentication (e.g. a local SMTP relay), leave `SMTP_USER` and `SMTP_PASSWORD` empty.

## Running

Start the server:

```
conda activate bgen
python app.py
```

The app runs at `http://localhost:5000`. On first startup it creates the SQLite database and the default admin user automatically.

## Docker deployment

Requires Docker and the Docker Compose plugin (`docker compose version` to check).

Build and start both services (app + MySQL):

```
docker compose up -d --build
```

Configuration is read from `.env` (`SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`) and from `MYSQL_ROOT_PASSWORD` / `MYSQL_PASSWORD` for the database. Copy `.env.example` to `.env` and adjust before deploying; unset variables fall back to defaults defined in `docker-compose.yml`.

The app runs at `http://localhost:5000`. On first startup it creates the database tables and the default admin user automatically. Data is persisted in the named volumes `mysql_data`, `qr_codes`, and `uploads`.

Useful commands:

```
docker compose logs -f app      # follow app logs
docker compose ps               # check status
docker compose stop             # stop services
docker compose down             # stop and remove containers
docker compose up -d --build    # rebuild after code changes
```
