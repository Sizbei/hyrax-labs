# backend-jvm — Kotlin + Java ingestion service
# Build + run the demo ingestion cycle on a JDK 17 base.
FROM eclipse-temurin:17-jdk AS base
WORKDIR /app

# Cache the Gradle wrapper + dependencies layer first.
COPY gradlew settings.gradle.kts build.gradle.kts ./
COPY gradle ./gradle
RUN chmod +x gradlew && ./gradlew --version --no-daemon

# Then the sources.
COPY src ./src

# Build (compiles + runs tests) so the image is known-good.
RUN ./gradlew build --no-daemon

# Default: run a demo ingestion cycle.
CMD ["./gradlew", "run", "--no-daemon", "-q"]
