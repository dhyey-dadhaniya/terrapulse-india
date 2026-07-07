# TerraPulse Backend

Spring Boot REST API for the TerraPulse India platform.

## Prerequisites

- Java 17+
- Maven 3.8+

## Run

```bash
mvn spring-boot:run
```

The backend starts at `http://localhost:8080`.

## Endpoints

| Method | Path      | Description  |
|--------|-----------|--------------|
| GET    | `/health` | Health check |

## Configuration

Update `src/main/resources/application.properties` with your PostgreSQL and Kafka connection details. Auto-configuration for these services is disabled by default so the app can start without them during local development.
