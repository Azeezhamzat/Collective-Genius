# Collective Genius

**Collective Genius** is a free, open-source platform for **collective intelligence** — structured tools that help any group think, decide and act together, at scale. Where it can be used for public participation and civic decision-making, it works just as well for a company's product roadmap, a research consortium's priorities, an open-source project's governance, a school's curriculum planning, or a neighborhood association's budget.

It is a rebuild of [adhocracy+](https://github.com/liqd/adhocracy-plus), originally built and maintained by [Liquid Democracy e.V.](https://liqd.net) for civic participation, and still built on [adhocracy 4](https://github.com/liqd/adhocracy4) and [Django](https://github.com/django/django). We are deeply grateful to the original authors — this project exists because of their work, and we aim to carry it forward for a wider range of groups and use cases. See [`docs/collective-intelligence-roadmap.md`](./docs/collective-intelligence-roadmap.md) for where this is headed.

## What it's for

Collective Genius gives any group a toolkit for going from many individual perspectives to a shared, legible outcome:

* **Idea generation** — open calls for ideas, geo-located proposals, structured briefs, with a ["check for similar ideas/proposals" step](./apps/deduplication) before submitting to cut down on near-duplicate entries
* **Deliberation** — threaded discussion, commenting on documents paragraph-by-paragraph (with automatic [revision history](./apps/documentrevisions) — every edit keeps its previous text), structured debates with [argument mapping](./apps/argumentmapping) showing where a debate's support actually concentrates
* **Prioritization** — voting, budgeting/resource allocation, topic prioritization, and [quadratic voting](./apps/quadraticvoting) (now configurable entirely from the project dashboard) for surfacing preference intensity, not just majority direction
* **Synthesis** — clustering related input and surfacing where a group actually agrees or disagrees (see [Synthesis](./apps/synthesis)), plus an automatic ["key points" summary](./apps/summarization) of any discussion (dependency-free by default, with an optional LLM-backed mode)
* **Decision-making** — polls, phased processes with clear timelines, moderator workflows, a project-wide [facilitator toolkit](./apps/facilitator) (activity overview, reported-comments queue), and [consent-based decisions](./apps/consent) (sociocracy/Loomio-style — a proposal passes once nobody has a standing objection, not because a majority likes it best)
* **Forecasting** — [prediction-market-style forecasting](./apps/forecasting) for questions with a checkable outcome: the crowd's aggregate probability estimate, plus a Brier-score leaderboard tracking who's actually well-calibrated over time, not just who guessed right once
* **Expert elicitation** — [Delphi-method rounds](./apps/delphi): anonymous numeric estimates, the group's aggregate shown back, revise and repeat — converges without anyone anchoring on who said what first
* **Organisation-wide search** — [semantic search](./apps/search) across every idea, proposal, map-idea and debate subject in every project an organisation runs, by meaning, not just exact keywords
* **Follow-through** — dashboards, exports, notifications, activity feeds
* **Cross-language groups** — [on-demand translation](./apps/translation) of discussion content (not just interface chrome) on the Synthesis and Summarization pages, so a multilingual group isn't stuck reading a discussion it can't follow

A "project" in Collective Genius is any structured process a group runs — it doesn't have to be a government initiative. An "organisation" is any group running processes — a company, a lab, a nonprofit, a DAO, a city council, or a community of volunteers.

## Getting started

### Requirements

* nodejs (+ npm)
* python 3.x (+ venv + pip)
* libpq (only if postgres should be used)

### Installation

    git clone https://github.com/Azeezhamzat/Collective-Genius.git
    cd Collective-Genius
    make install
    make fixtures

### Start virtual environment

    source venv/bin/activate

### Check if tests work

    make test

### Start a local server

    make watch

### Use postgresql database for testing

Run the following command once:

    make create-postgres

To start the testserver with postgresql, run:

    export DATABASE=postgresql
    make start-postgres
    make watch

Go to <http://localhost:8004/> and log in with the admin credentials from your local fixtures.

## Installation on a production system

An installation guide for production systems can be found [here](./docs/installation_prod.md).

## Roadmap

We're rebuilding this platform to be the best general-purpose collective intelligence tool available — not just for civic participation, but for any group that needs to think and decide together. See [`docs/collective-intelligence-roadmap.md`](./docs/collective-intelligence-roadmap.md) for the full feature roadmap, organized by priority.

## Contributing or maintaining your own fork

If you found an issue, want to contribute, or would like to add your own features to your own version of Collective Genius, check out [contributing](./docs/contributing.md). Building a new participation module (a new voting method, a new visualization)? See [`docs/building_a_module.md`](./docs/building_a_module.md) — a practical guide written from having built eight of them.

## Attribution

Collective Genius is a derivative work of [adhocracy+](https://github.com/liqd/adhocracy-plus) (AGPL-3.0+), created by Liquid Democracy e.V. It remains licensed under AGPL-3.0+; see [`LICENSE`](./LICENSE).

## Security

We care about security. If you find any issues concerning security, please open a private security advisory on this repository rather than a public issue.
