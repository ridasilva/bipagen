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

## Running

Start the server:

```
conda activate bgen
python app.py
```

The app runs at `http://localhost:5002`. On first startup it creates the SQLite database and the default admin user automatically.
