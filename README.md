# microblog-api
An modern (as of 2022) Flask API back end.

## Deploy to Heroku

Click the button below to deploy the application directly to your Heroku
account.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/miguelgrinberg/microblog-api/tree/heroku)

## Deploy on your Computer

### Setup

Follow these steps if you want to run this application on your computer, either
in a Docker container or as a standalone Python application.

```bash
git clone https://github.com/miguelgrinberg/microblog-api
cd microblog-api
cp .env.example .env
```

Open the new `.env` file and enter values for the configuration variables.

### Run with Docker

To start:

```bash
docker-compose up -d
```

The application runs on port 5000 on your Docker host. You can access the API
documentation on the `/docs` URL (i.e. `http://localhost:5000/docs` if you are
running Docker locally).

To populate the database with some randomly generated data:

```bash
docker-compose run --rm microblog-api bash -c "flask fake users 10 && flask fake posts 100"
```

To stop the application:

```bash
docker-compose down
```

### Run locally

Set up a Python 3 virtualenv and install the dependencies on it:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create the database and populate it with some randomly generated data:

```bash
flask db upgrade
flask fake users 10
flask fake posts 100
```

Run the application with the Flask development web server:

```bash
flask run
```

The application runs on `localhost:5000`. You can access the API documentation
at `http://localhost:5000/docs`.
