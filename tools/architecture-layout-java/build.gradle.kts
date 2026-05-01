plugins {
    application
    java
}

group = "com.souroldgeezer.architecture"
version = "0.21.0"

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

application {
    mainClass.set("com.souroldgeezer.architecture.layout.ArchLayoutCli")
}

dependencies {
    implementation("info.picocli:picocli:4.7.6")
    implementation("com.fasterxml.jackson.core:jackson-databind:2.17.2")
    implementation("com.networknt:json-schema-validator:2.0.1")
    implementation("org.eclipse.elk:org.eclipse.elk.core:0.11.0")
    implementation("org.eclipse.elk:org.eclipse.elk.graph:0.11.0")
    implementation("org.eclipse.elk:org.eclipse.elk.alg.layered:0.11.0")
    implementation("org.eclipse.xtext:org.eclipse.xtext.xbase.lib:2.32.0")
    runtimeOnly("org.slf4j:slf4j-nop:2.0.13")

    testImplementation("org.junit.jupiter:junit-jupiter:5.10.3")
    testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine:5.10.3")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:1.10.3")
}

tasks.test {
    useJUnitPlatform()
}

tasks.register<Jar>("runtimeJar") {
    archiveFileName.set("arch-layout.jar")
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    exclude("META-INF/*.SF", "META-INF/*.DSA", "META-INF/*.RSA")
    manifest {
        attributes["Main-Class"] = application.mainClass.get()
    }
    from(sourceSets.main.get().output)
    from({
        configurations.runtimeClasspath.get().map { dependency ->
            if (dependency.isDirectory) dependency else zipTree(dependency)
        }
    })
}
