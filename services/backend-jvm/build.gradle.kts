plugins {
    kotlin("jvm") version "1.9.24"
    application
}

group = "com.hyraxlabs"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencies {
    // Asynchronous / coroutine-based scheduling
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.1")

    // Logging facade + lightweight binding
    implementation("org.slf4j:slf4j-api:2.0.13")
    implementation("org.slf4j:slf4j-simple:2.0.13")

    // Testing
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:1.10.2")
}

// Java 17 toolchain for both Kotlin and Java sources.
kotlin {
    jvmToolchain(17)
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

application {
    mainClass.set("com.hyraxlabs.ingest.AppKt")
}

tasks.test {
    useJUnitPlatform()
    testLogging {
        events("passed", "skipped", "failed")
    }
}
