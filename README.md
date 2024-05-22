# Calendarium

This is a simple Flask web application designed for tracking and managing event data, featuring a dynamic timeline view.

## Getting Started

To get the application running locally:

```bash
docker-compose up --build
```

The app will be available at [http://localhost:5001/](http://localhost:5001/).

### Filling the App with Sample Data

To populate the application with sample data, run:

```bash
curl -X POST http://localhost:5001/batch-import -H "Content-Type: application/json" -d @testdata.json
```

## API Endpoints

Below are the available API endpoints with their respective usage:

- **Home**
  - **GET** `/`
  - Returns the main page of the application.

- **Timeline**
  - **GET** `/timeline?timeline-height=<height>&font-family=<font>&font-scale=<scale>`
  - Displays a timeline of all entries. Allows optional `timeline-height`, `font-family`, and `font-scale` query parameters to adjust the height of the timeline, set the font, and apply a scale factor to the font size respectively (e.g., `timeline-height=100%`, `font-family=Arial`, `font-scale=1.5`). This view uses the Flickity library.

- **Create Entry**
  - **POST** `/create`
  - Creates a new entry. Requires form data including `date`, `category`, `title`, and `description`.

- **Update Entry**
  - **GET/POST** `/update/<int:id>`
  - Retrieves an entry for editing or updates an entry if POST method is used.

- **Delete Entry**
  - **POST** `/delete/<int:id>`
  - Deletes an entry by ID.

- **API Data Access**
  - **GET** `/api/data`
  - Returns all entries in JSON format, including additional attributes such as `date_formatted` and `index` which help in sorting and formatting entries relative to the current date.

- **Export Data**
  - **GET** `/export-data`
  - Exports all entries and associated images as a zip file.

- **Batch Import**
  - **POST** `/batch-import`
  - Imports a batch of entries from a JSON file.

- **Update Birthdays**
  - **PUT** `/update-birthdays`
  - Updates all birthday entries to the current year.

- **Purge Old Entries**
  - **POST** `/purge-old-entries`
  - Deletes all entries where the date is in the past and the category is not 'birthday'.

## Grafana Integration

This application supports integration with Grafana through a Simple JSON Datasource, enabling Grafana to pull data for visualization purposes. Here are the endpoints provided for Grafana:

### Grafana Endpoint Descriptions

- **Test Connection** (`GET /grafana/`)
  - Confirms the data source connection is functional.
  
- **Search** (`POST /grafana/search`)
  - Returns a list of categories that can be queried (e.g., 'cake', 'birthday').

- **Query** (`POST /grafana/query`)
  - Retrieves timeseries data based on specified categories.

- **Annotations** (`POST /grafana/annotations`)
  - Delivers event annotations for graph overlays based on specific queries.

- **Tag Keys** (`POST /grafana/tag-keys`)
  - Provides tag keys for Grafana's ad hoc filtering capabilities.

- **Tag Values** (`POST /grafana/tag-values`)
  - Supplies values for the selected tag keys for further filtering.

### Example Usage

Query Grafana for timeseries data in the 'cake' category using this `curl` command:

```bash
curl -X POST http://127.0.0.1:5000/grafana/query -H "Content-Type: application/json" -d '{"targets":[{"target": "cake", "type": "timeserie"}]}'
```

This command will return timeseries data points for the 'cake' category if such data exists. Ensure the Grafana Simple JSON Datasource plugin is installed and properly configured to interact with these endpoints.

## Flickity License Information

This project uses Flickity, which is licensed under the GPLv3. As such, modifications to the Flickity source code used in this project are documented in the repository. To comply with the GPLv3, all source code for this application is available under the same license. The full license text is included in the LICENSE file in this repository.

## Docker Image
You can pull the Docker image for this project from Docker Hub:
[Docker Hub Repository](https://hub.docker.com/r/whustedt/calendarium)
