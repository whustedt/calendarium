# Grafana 13 integration

Calendarium provides a read-only REST API through **Infinity**, maintained by
Grafana Labs. Use its **Backend → JSONata** parser (the saved query value is
`backend`). This runs HTTP requests and data-frame conversion inside Grafana,
works without AngularJS or the retired Simple JSON protocol, and supports
server-side alert queries as well as dashboards.

Official references: [Infinity documentation](https://grafana.com/docs/plugins/yesoreyeram-infinity-datasource/latest/),
[backend parser](https://grafana.com/docs/plugins/yesoreyeram-infinity-datasource/latest/query/backend/),
[time macros](https://grafana.com/docs/plugins/yesoreyeram-infinity-datasource/latest/query/macros/),
and [annotations](https://grafana.com/docs/plugins/yesoreyeram-infinity-datasource/latest/annotations/).

## Install and provision

1. Install the current signed `yesoreyeram-infinity-datasource` plugin on your
   Grafana 13 server, using the plugin catalog or Grafana's supported plugin
   installation mechanism, and restart Grafana if required. Do not install the
   old Simple JSON or JSON API plugin.
2. Set `CALENDARIUM_URL` **in Grafana's environment** to the Calendarium origin,
   without a trailing slash. With this repository's Docker Compose networking,
   it is `http://web:8000`. Grafana must share that network; `localhost` inside a
   Grafana container refers to Grafana itself. For a remote deployment use the
   HTTPS URL reachable by the Grafana backend. A reverse-proxy path prefix can
   be included, for example `https://example.com/calendarium`.
3. Copy or mount `provisioning/datasources/calendarium.yaml` into
   `/etc/grafana/provisioning/datasources/`.
4. Copy or mount `provisioning/dashboards/calendarium.yaml` into
   `/etc/grafana/provisioning/dashboards/` and `dashboards/calendarium.json` into
   `/var/lib/grafana/dashboards/calendarium/`. Provisioning uses the fixed data
   source UID `calendarium`.
5. Restart Grafana. Run **Save & test** on the Calendarium data source; it calls
   the API's database health check. Open the **Calendarium** dashboard in the
   **Calendarium** folder and select a range containing events.

Alternatively, create an Infinity data source manually with UID `calendarium`,
base URL `<CALENDARIUM_URL>/api/grafana/v1`, and the Calendarium origin in
**Allowed hosts**. Enable a custom health check at
`<CALENDARIUM_URL>/api/grafana/v1/health`. Import `dashboards/calendarium.json`.
The provided dashboard includes category selection, an event-count chart, an
event table, and event annotations.

The example provisioning uses no authentication, matching the rest of the
application's existing network-based access model. Keep the service on a trusted
network or enable the token below. HTTP calls come from Grafana's backend;
no browser CORS configuration is needed.

## Optional bearer authentication

Set `GRAFANA_API_TOKEN` in **Calendarium's environment** to require
`Authorization: Bearer <token>` on **all** `/api/grafana/v1/*` routes, including
health and category queries. Restart Calendarium after changing it. Tokens in
query parameters are not supported. If unset, these read-only routes are open.
This token protects only this integration; it does not authenticate other
Calendarium routes.

In Infinity, choose **Bearer token** and store the same token in the secure
configuration. For provisioning, change the data source's `jsonData.auth_method`
from `none` to `bearerToken`, and add this at the data-source level:

```yaml
    secureJsonData:
      bearerToken: $GRAFANA_API_TOKEN
```

Supply that variable separately to the Grafana process through your secret
manager. Keep token values out of dashboard JSON, URLs, and committed files.
The `$VAR` form avoids a second expansion of `$` characters inside Grafana
provisioning secret values. Keep TLS verification enabled when using HTTPS.

## HTTP API

Base path: **`/api/grafana/v1`**. All endpoints are `GET` and return JSON.
All array responses are flat arrays, ready for Infinity's root selector `$`.

| Path | Result | Infinity format |
| --- | --- | --- |
| `/health` | `{"status":"ok","api_version":1}` after a database query | Health check |
| `/categories` | Category `id`, `name`, `symbol`, `color`, `repeat_annually` | Table / query variable |
| `/events` | One row per event occurrence, ordered by time, category, ID | Table |
| `/timeseries` | Rows with `time`, `category`, `count`, ordered by time and category | Time series |
| `/annotations` | Rows with `time`, `title`, `text`, `tags` | Data Frame |

### Time range and filters

`/events`, `/timeseries`, and `/annotations` require these two parameters:

| Parameter | Description |
| --- | --- |
| `from` | Inclusive start: Unix **milliseconds** or ISO 8601 with an explicit timezone, e.g. `2025-01-01T00:00:00Z` |
| `to` | Inclusive end, in the same supported formats |

Optional parameters shared by these three endpoints:

| Parameter | Description |
| --- | --- |
| `category` | Exact category name; repeat the parameter to select multiple names. Omit to select all. |
| `categories` | A JSON array of exact names, e.g. `["Birthday","Release"]`. Use this with Grafana multi-value variables. Mutually exclusive with `category`. An empty array selects no categories. |
| `timezone` | IANA timezone for calendar dates and aggregation, default `GRAFANA_TIMEZONE` or `Europe/Berlin`. |
| `include_cancelled` | `true` or `false`; default `false`. Applies equally to tables, counts, and annotations. |

`/timeseries` also accepts `interval=day` (default), `week` (Monday start), or
`month` (calendar month). Counts include zeroes for every selected category and
bucket, even when it has no events. Only events inside the requested range are
counted. Bucket timestamps are local calendar midnights converted to epoch
milliseconds; the first bucket is clipped to `from` if its start is earlier.
Days spanning a daylight-saving transition therefore need not be 24 hours long.

Dates in Calendarium have no time of day. An event occurs at midnight in the
selected calendar timezone and is included only when that instant lies inside
`[from, to]`. Use whole-day dashboard ranges to include all events on a date.
The included dashboard uses `Europe/Berlin` both for display and for API queries;
change both settings if you need another calendar timezone.

Annual categories expand into **every occurrence in the requested range**, not
just the next occurrence relative to today. Occurrences before the stored
original year are excluded. February 29 falls on February 28 in non-leap years.
Year `0001` retains the application's unknown-birth-year convention and produces
no anniversary age. Counts, tables, and annotations use the same calendar rules.
Malformed dates in legacy data are skipped with a server log warning.

### Event and annotation fields

`/events` returns:

- `id` (stored event ID), `time` (integer epoch milliseconds), `date` (occurrence
  date), `original_date` (stored date).
- `title`, `description` (empty string when absent), `category`, `category_id`,
  `symbol`, `color`, `url` (nullable), `recurring`, `cancelled`.
- `years_since`, `milestone_year` (nullable), and `is_milestone`, using the same
  anniversary calculation as the application.

The same `id` can occur in different years; `(id, date)` identifies an occurrence.
`/annotations` includes the title in `text` along with the optional description,
so it remains visible when only Grafana's standard text field is mapped. Its
`tags` field is a comma-separated string as expected by Infinity annotations.
Category names containing commas remain exact in event filters and tables, but
Grafana displays those annotation tags as multiple tags.

### Errors and limits

Errors are JSON objects with an `error` string:

- `400`: missing/invalid range, reversed bounds, unknown or duplicate scalar
  parameters, invalid timezone, unsupported interval, or malformed filters.
- `401`: missing or incorrect token when authentication is configured.
- `422`: result or processing budget exceeded. Narrow the range/categories or
  use a coarser time-series interval. Results are never silently truncated.
- `503`: database query failed; internal error details remain in server logs.

Ranges are limited to 3660 days, category filters to 100 names, response rows to
10,000, and event expansion to 50,000 occurrences per request. All responses have
`Cache-Control: no-store`. Empty event/annotation results and unknown categories
return `[]`; known categories with no events still return zero-filled counts.

Example, without authentication:

```bash
curl --get 'http://127.0.0.1:5000/api/grafana/v1/events' \
  --data-urlencode 'from=2025-01-01T00:00:00Z' \
  --data-urlencode 'to=2025-12-31T23:59:59.999Z' \
  --data-urlencode 'categories=["Birthday","Release"]'
```

## Building queries and alerts

For each query select **Type: JSON**, **Source: URL**, **Parser: Backend → JSONata**,
and root selector `$`. Use URL options to add parameters; Infinity URL-encodes
them, including quotes, spaces, ampersands, and commas inside category names.

Use `${__timeFrom}` and `${__timeTo}` for `from` and `to`. These are Infinity's
**backend** time macros and also work for server-side queries. For a multi-value
category variable use `${categories:json}` as the `categories` parameter. Leave
**Custom all value** empty so Grafana expands **All** into a JSON array of names.
For category-variable queries, map `name` to string columns `__text` and
`__value` and use the `/categories` endpoint.

Column mapping:

| Endpoint | Selector → column name (type) | Format |
| --- | --- | --- |
| `/timeseries` | `time` → `time` (Time / UNIX ms), `category` → `category` (String), `count` → `count` (Number) | Time series |
| `/events` | `time` → `Date` (Time / UNIX ms), `title` → `Title` (String), plus any event fields needed | Table |
| `/annotations` | `time` → `time` (Time / UNIX ms), `title` → `title`, `text` → `text`, `tags` → `tags` (String) | Data Frame |

In saved JSON, **Time / UNIX ms** is `timestamp_epoch`; **Data Frame** is
`dataframe`. Backend time-series queries convert the sorted long-form result
into Grafana series labelled by category. No panel-side transformation is needed.
The example dashboard automatically switches from daily to weekly and monthly
counts for longer ranges.

For Grafana-managed alerts, use `/timeseries`, keep the backend parser, and set
literal category filters or omit them. Dashboard variables are not available to
alert evaluation. Retain the backend time macros and choose an appropriate
calendar interval. Apply a Grafana reduce/threshold expression to the numeric
series. Zero-filled buckets allow categories without events to evaluate as zero.

## Migrating from Simple JSON

This is a breaking replacement: `/grafana/`, `/grafana/search`, `/grafana/query`,
`/grafana/annotations`, `/grafana/tag-keys`, and `/grafana/tag-values` are removed
and return 404. There is no Simple JSON compatibility mode.

1. Replace the Simple JSON data source with Infinity and provision the new API
   base URL and optional bearer token.
2. Replace target searches and category tag-value queries with `/categories`
   query variables. Replace ad-hoc tag filters with the dashboard category
   variable or explicit REST query parameters.
3. Replace `POST /query` payloads with `/timeseries` GET queries and pass the
   dashboard range explicitly. The old route ignored the range; the replacement
   filters it. Timestamps are now explicitly timezone-aware.
4. Replace annotation requests with `/annotations` using Data Frame format and
   the mappings above. Use `/events` for event tables.
5. Import the included dashboard or update existing panels. Remove the old
   Simple JSON plugin once no dashboards use it.

Validate the API with `python -m pytest tests/test_routes_grafana.py` from the
repository root in the configured Python environment.

The integration was also verified with **Grafana 13.3.0** and the signed
**Infinity 4.1.6** release: data-source and dashboard provisioning, the health
check, all four backend query shapes, rendering in Chromium, and category
variable interpolation including names with commas, Unicode, and quotes.
Bearer-authenticated health checks and event queries were verified through
Infinity as well.
