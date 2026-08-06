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

## Testing

Unit and integration testing of the backend is accomplished through Pytest. In an environment with Pytest, run 'pytest ./backend' from the project's root directory.

Integration testing expects a test database with the following parameters:

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
    CREATE EXTENSION postgis;
```
