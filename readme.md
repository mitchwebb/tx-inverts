# Source Code for Texas Inverts

This repo holds the source code for the Texas Inverts website. The site is built to provide preliminary, approximate conservation rankings for the invertebrate species of Texas to help in Texas Parks and Wildlife's effort to track Species of Greatest Conservation Need. This site is built on public data from the GBIF database and runs period download/updates for presentation and querying. All of the data is public.

## Implementation

The site is written in TypeScript, Python, Svelte, and PostgreSQL. These tools were selected in part to mimic other related resources (https://github.com/ut-entomology/cavesite), as well as in an effort to make a clear, accessible, and maintainable product.

As a note: while Svelte may not share the ubiquity of TypeScript, Python, or PostgreSQL, it was chosen as a cleaner, easier-to-learn alternative to React. Though there is still a learning curve, it should be easier to pick up for anyone interacting with this code who is new to front-end frameworks.

## Installation

To install the site on a publicly available server, follow the instructions in the ~~installation manual~~ (coming soon).

```
    GBIF__USER='************'
    GBIF__EMAIL='************'
    GBIF__PASSWORD='************'

    DATABASE__USER='************'
    DATABASE__PASSWORD='************'
    DATABASE__HOST='************'
    DATABASE__PORT='************'
    DATABASE__NAME='************'

    CORS__DOMAIN='************'
```

## Development Installation

When trying to install the source locally, you'll need to verify that you have access to the following:

- A working environment with Python and pip
- The NPM package manager
- TypeScript
- PostgreSQL and psql with PostGIS available

Now, wherever you want the project to live, git clone this repo. The project will clone in a directory called `tx-inverts`.

## Configuring Your Environment

You can install packages related to the frontend by running `npm install` from the `tx-inverts/frontend` directory. Make sure your NodeJS and npm versions are up to date—otherwise this install can fail ambiguously.

Likewise, you can install packages related to the backend by running `pip install -r ./requirements.txt` from the `tx-inverts/backend` directory. It's recommended that you do this within an environment.

Next you'll need to set up some environment variables.
You can do so by making a file at `tx-inverts/.env`. In this file, you'll need the following fields:

```
# GBIF
GBIF__USER=your-gbif-username
GBIF__EMAIL=your-gbif-email
GBIF__PASSWORD=your-gbif-password

# (Optional, for the GBIF test API)
GBIF__UAT_USER=your-gbif-username
GBIF__UAT_EMAIL=your-gbif-email
GBIF__UAT_PASSWORD=your-gbif-password

# PostgreSQL
DATABASE__USER=postgres-username
DATABASE__PASSWORD=postgres-user-password
DATABASE__HOST='localhost'
DATABASE__PORT='5432'
DATABASE__NAME='txinverts' (or whatever you've named your database)

# CORS
CORS__DOMAIN='http://localhost:5173' (or wherever your frontend exists)
```

You'll also need a couple frontend variables for VITE. Place these in `tx-inverts/frontend/.env`:

```
# MapBox
VITE_MAPBOX_TOKEN=your-mapbox-access-token

# VITE
VITE_API_PROXY='http://127.0.0.1:8000' (or wherever your backend exists)
```

## PostgreSQL Extensions

If PostgreSQL is running on your machine without either PostGIS or pg_trgm, you'll need these.
In case PostGIS isn't on your machine at all, you'll need to install it. This should be possible on linux machines with `apt install postgis` or on Windows machines through their website and installer.

After this, run

```
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

on your txinverts database to make sure these extensions are enabled.

## App Setup

Now you should be ready to run the initial app setup using `python -m backend.jobs.runners.run_setup`.

This runner can take multiple hours and accomplishes the following:

- Basic table creation
- Index initialization
- Request, download, and insertion of GBIF data for the following tables:
    - us_invasives_checklist (for flagging invasive species)
    - gbif_inverts_backbone (all taxonomic information for inverts currently in use on GBIF)
    - gbif_observations (all gbif observations for inverts in simple Texas bounding box—2+ GB)
        - During this ingestion, observations are processed in an attempt to retrieve lost date information, and to restrict them to a full-resolution Texas shapefile
- Populating of shapefile tables (for filtering observations)
- Generation of tx_taxa table (containing only taxa represented by cleaned Texas observations)
- Generation of taxon_lineage and taxon_region_presence tables, allowing for easier lookups
- Generation of map tiles for largest taxa (to help speed up expensive rendering)
- Calculation of basic conservation rankings for all invertebrate taxa found in Texas
- Generation of observations_regions table, which ties each observation to corresponding regions of interest

The terminal in which this runner is launched will output logs as the individual tasks are run.

Note: While the GBIF download API usually takes ≈15 minutes to process a download request, on some occasions it can take much longer. This can lead this process to take hours longer while waiting for GBIF requests to process.

## Run the App

At this point, you should be good to go. In Windows, you can run the app from `tx-inverts/` using `run` in the terminal to run a combo `run.bat` file. This will open both the backend and frontend processes, which will show you where your app is running.

On Linux, you can run using `bash runSvelte.sh` in a terminal for the frontend and `bash runUvicorn.sh` in another terminal for the backend.

## Testing

Unit and integration testing of the backend is accomplished through Pytest.
Integration testing expects an existing test database with the following parameters:

```
    host: 'localhost',
    database: 'test_inverts',
    port: 5432,
    user: 'test_user',
    password: 'test_pass'
```

With a PostgreSQL server running on the port specified above, a functioning test database can be created using the following SQL:

```
    CREATE DATABASE test_inverts;
    CREATE USER test_user WITH ENCRYPTED PASSWORD 'test_pass';
    ALTER SCHEMA public OWNER TO test_user;
    GRANT ALL PRIVILEGES ON DATABASE test_inverts TO test_user;
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

From here, run 'pytest ./backend' from the project's root directory.

To run frontend testing, run `npm run vitest` from the `tx-inverts/frontend` directory.
