import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// La versión es la misma que la del programa de la PC (version.py).
val versionPC = Regex("VERSION = \"([\\d.]+)\"").find(rootDir.resolve("../version.py").readText())!!.groupValues[1]
val numeros = versionPC.split(".").map { it.toInt() }

// La firma de la app vive FUERA del repo (herramientas/armar_apk.bat la crea y la indica con CONTROL_FIRMA).
// Hay que usar siempre la misma: si cambia, Android no deja actualizar la app (hay que desinstalarla antes).
val firma = Properties().apply {
    System.getenv("CONTROL_FIRMA")?.let { ruta -> file(ruta).takeIf { it.exists() }?.inputStream()?.use { load(it) } }
}

android {
    namespace = "io.github.workon2027.controlcelular"
    compileSdk = 34

    defaultConfig {
        applicationId = "io.github.workon2027.controlcelular"
        minSdk = 26
        targetSdk = 34
        versionCode = numeros[0] * 10000 + numeros[1] * 100 + numeros[2]
        versionName = versionPC
    }

    signingConfigs {
        if (!firma.isEmpty) {
            create("publicar") {
                storeFile = file(firma.getProperty("archivo"))
                storePassword = firma.getProperty("clave")
                keyAlias = firma.getProperty("alias")
                keyPassword = firma.getProperty("clave")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("publicar") ?: signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    // La página del control es la misma que sirve la PC (carpeta web/): la app la lleva adentro.
    sourceSets["main"].assets.srcDirs(rootDir.resolve("../web"))
}

dependencies {
    implementation("androidx.webkit:webkit:1.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
