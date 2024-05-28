# Calendarium

This is a simple Flask web application designed for tracking and managing event data, featuring a dynamic timeline view.

## Getting Started

To get the application running locally, you have several options:

### Using Docker

```bash
docker-compose up --build
```

The app will be available at [http://localhost:5001/](http://localhost:5001/).

### Using a Development Container or Python Environment

Alternatively, you can set up a development container or any other Python environment. After setting up, start the application with the following command:

```bash
flask run --debug
```

Ensure your environment has all the necessary dependencies installed as specified in the `requirements.txt` file.

### Environment Variables

To integrate with Giphy, create a `.env` file in the project root and add the following key:

```plaintext
GIPHY_API_TOKEN=<your_giphy_api_token>
```

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

## Giphy Integration

The Calendarium application features integration with the Giphy API to enhance the user interface with dynamic content. There are two different implementations of this integration, tailored to different deployment environments and security concerns.

### Direct Backend Integration (Original Version)

In environments where the backend server has internet access, the application can directly interact with the Giphy API. This method involves the backend making API requests to Giphy and securely managing the API key via environment variables.

- **Endpoint**: `/search_gifs`
- **Method**: `GET`
- **Function**: This endpoint takes a search query as a parameter, directly calls the Giphy API, and returns the GIF data. This keeps the API key secure and not exposed to the client-side.

Example usage:
```bash
curl http://localhost:5001/search_gifs?q=cats
```
This implementation is found in the JavaScript file `search_gifs.js`.

### Proxied API Integration (New Version)

For environments where the backend does not have direct internet access, we employ a proxied approach. Here, the backend generates a URL with the API key, which is then used by the frontend to make the Giphy API call. This method ensures that the API key is not exposed in the client-side code.

- **Backend Endpoint**: `/get-giphy-url`
- **Method**: `GET`
- **Function**: This endpoint constructs the request URL including the API key and returns it to the client. The client then uses this URL to fetch GIF data directly from Giphy.

Example usage:
```bash
curl http://localhost:5001/get-giphy-url?q=cats
```
This implementation is located in the JavaScript file `search_gifs_proxied.js`.

These methods are designed to accommodate different network security policies while maintaining functionality and protecting sensitive information.

## Flickity License Information

This project uses Flickity, which is licensed under the GPLv3.

 As such, modifications to the Flickity source code used in this project are documented in the repository. To comply with the GPLv3, all source code for this application is available under the same license. The full license text is included in the LICENSE file in this repository.

## Docker Image

Instead of Docker Hub, this project's Docker images are now built and pushed through GitHub Actions to the GitHub Container Registry.