# Calendar & Weather Dashboard Application (Docker Hub Edition)

## Overview

This application is a web-based dashboard that displays calendar events from multiple iCalendar (ICS) feeds and a local weather widget. It's designed to be run as a Docker container pulled directly from Docker Hub, making deployment quick and straightforward. The dashboard provides a consolidated view of upcoming events and current/forecasted weather for a specified location. Background images rotate periodically to provide a dynamic visual experience.

## Features

*   **Aggregated Calendar View:** Displays events from multiple ICS URLs for the next 7 days.
    *   Each calendar source is color-coded for easy identification.
    *   A legend displays the name of each calendar and its associated color.
    *   Correctly handles all-day and multi-day events, showing appropriate durations (e.g., "All-Day", "X days").
    *   Formats event start times clearly (Date for all-day events, Date + Time for specific-time events in the configured local timezone).
*   **Weather Widget:**
    *   Shows current weather conditions (temperature, description, icon).
    *   Displays a 24-hour forecast at 4-hour intervals.
    *   Weather data is fetched from OpenWeatherMap API.
*   **Dynamic Background:** Rotates background images from a specified local directory.
*   **Configurable:** Key settings like API keys, geo-coordinates for weather, and calendar URLs are read from external configuration files, making the container highly configurable at runtime by mounting local files.

## Requirements for Running

1.  **Docker Installed:** You need Docker installed on your system to pull and run the container image.
2.  **External Configuration Files & Directories:**
    This application reads its configuration from files and directories that you provide from your host machine and mount into the container. Before running the container, create a directory on your host (e.g., `/path/to/your/calendar_config_files`) with the following structure and content:

    ```
    /path/to/your/calendar_config_files/
    ├── ics/
    │   └── ics_urls.txt
    ├── config/
    │   ├── weather_api_key.txt
    │   └── geo_coordinates.txt
    └── images/
        └── your_image1.jpg
        └── your_image2.png
        └── (...)
    ```

    *   **`ics/ics_urls.txt`**: A plain text file. Each line should be a URL to an iCalendar (`.ics`) feed you want to display. For example:
        ```text
        https://calendar.google.com/calendar/ical/example1%40gmail.com/private-abcdef1234567890/basic.ics
        https://calendar.google.com/calendar/ical/example2%40outlook.com/private-qwerty0987654321/basic.ics
        ```
        Place this file in the `ics` folder within your main configuration directory.

    *   **`config/weather_api_key.txt`**: A plain text file containing only your OpenWeatherMap API key. You can obtain one from [OpenWeatherMap](https://openweathermap.org/appid).

    *   **`config/geo_coordinates.txt`**: A plain text file with two lines:
        *   Line 1: Latitude for the weather forecast (e.g., `30.2672`)
        *   Line 2: Longitude for the weather forecast (e.g., `-97.7431`)

    *   **`images/`**: A directory containing the background images you want the dashboard to display (e.g., `.jpg`, `.png`, `.gif`).

## How to Run from Docker Hub

1.  **Prepare External Configuration & Static Files:**
    Create the directory structure (`ics`, `config`, `images`) and the necessary configuration files on your host machine as described in the "Requirements" section. For example, you might create a main directory like `/home/user/my_calendar_dashboard_data`.

2.  **Pull the Docker Image:**
    Open your terminal and pull the latest image from Docker Hub:
    ```bash
    docker pull swedebear/dakilla:latest
    ```
    *(You can also pull a specific version, e.g., `docker pull swedebear/dakilla:1.0.2`)*

3.  **Run the Docker Container:**
    Use the following command to run the container. **Remember to replace `/path/to/your/calendar_config_files` with the actual, absolute path on your host system where you stored your configuration files and directories.**
    ```bash
    docker run -d \
        -p 8000:8000 \
        -v /path/to/your/calendar_config_files:/calendar/static \
        --name family-calendar \
        swedebear/dakilla:latest
    ```
    *   `-d`: Runs the container in detached (background) mode.
    *   `-p 8000:8000`: Maps port 8000 on your host machine to port 8000 inside the container.
    *   `-v /path/to/your/calendar_config_files:/calendar/static`: **Crucial step!** This mounts your local directory (which contains the `ics`, `config`, and `images` subdirectories) into the `/calendar/static` directory inside the container.
    *   `--name family-calendar`: Assigns a name to your running container.
    *   `swedebear/dakilla:latest`: Specifies the Docker image to use.

4.  **Access the Application:**
    Open your web browser and navigate to `http://localhost:8000`.

## Key Configuration Points (via Mounted Files)

The application expects to find its configuration files within the directory you mount to `/calendar/static` inside the container.

*   **Calendar Feeds:** Path on host: `/path/to/your/calendar_config_files/ics/ics_urls.txt`
*   **Weather API Key:** Path on host: `/path/to/your/calendar_config_files/config/weather_api_key.txt`
*   **Weather Location:** Path on host: `/path/to/your/calendar_config_files/config/geo_coordinates.txt`
*   **Background Images:** Path on host: `/path/to/your/calendar_config_files/images/`

This setup allows you to easily manage your calendar sources, API key, location, and images by simply editing the files on your host machine. If you make changes to these configuration files, you typically need to restart the Docker container for the application to pick them up:
```bash
docker restart family-calendar
```

---
Let me know how you like it: dghovd@gmail.com
