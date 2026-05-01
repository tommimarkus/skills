pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}

buildCache {
    local {
        directory = file("../../.cache/gradle/architecture-layout-java/build-cache")
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        mavenCentral()
    }
}

rootProject.name = "architecture-layout-java"
