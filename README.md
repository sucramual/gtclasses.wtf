# [gtclasses.wtf](https://gtclasses-wtf.fly.dev/)

_I just want to take a class about **[X]** but searching ~~Harvard~~ Georgia Tech’s course catalog is slow and the results are noisy. WTF?_

This is a Georgia Tech–adapted fork of Eric Zhang’s original [**classes.wtf**](https://github.com/ekzhang/classes.wtf) (built for Harvard). I ported it because finding classes through the official search flow felt painfully slow and inefficient. Course data is gathered via the [**gt-scheduler crawler**](https://github.com/gt-scheduler/crawler-v2) (used here to crawl raw class data).

Feedback? Email me at ylau36 at gatech dot edu

## How does it work?

**classes.wtf** is a fast search engine written in [Go](https://go.dev/), optimized for low-latency and high-quality results. It uses an in-memory [Redis](https://redis.io/) index (run as a subprocess) to support full-text fuzzy and prefix search across fields, plus a rich query syntax.

The frontend is a static site built with [Svelte](https://svelte.dev/), issuing searches on every keystroke with the goal that the full {request → compute → response → render} pipeline stays under ~30ms.

## Development

You need [Go 1.20](https://go.dev/) and [Docker](https://www.docker.com/) for the backend, [Node.js v18](https://nodejs.org/en/) for the frontend and crawler, and Python 3 for the bridge script.

### Getting course data (Georgia Tech)

Pipeline:

1. Run the GT crawler (`crawler-v2`)
2. Convert crawler output with the bridge script
3. Combine term files into a searchable dataset

#### 1) Run the GT crawler (crawler-v2)

```bash
cd crawler-v2
npm ci
npm run start
```

This writes term files into the repo root `data/` as `data/YYYYMM.json`.

````

#### 2) Convert with the bridge

```bash
cd ..
python3 bridge.py                                   # converts all data/YYYYMM.json
python3 bridge.py data/202602.json data/202608.json # converts data from specific term
````

This writes `data/courses-YYYYMM-.json` files.

#### 3) Combine data

```bash
go run . combine
```

This merges all `data/courses-*.json` files into a single `data/courses.json` used by the webapp.

### Running the server

The server listens on port 7500. (It also spawns a Redis instance via Docker on port 7501.)

```bash
go run . server -local -data data/courses.json
```

Develop the frontend (proxies API requests to the server):

```bash
npm install
npm run dev
```

Visit `localhost:5173`.

### Building a container

```bash
docker build -t classes.wtf .
docker run -it --rm -p 7500:7500 classes.wtf
```

### Deployment

```bash
fly deploy
```

## Acknowledgements

Original project by Eric Zhang (Harvard): see the upstream contributors page. Licensed under the [MIT license](LICENSE).
