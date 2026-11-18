plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}

// El armado va fuera de la carpeta del proyecto: OneDrive traba las carpetas con muchos archivos que cambian.
val afuera = System.getenv("CONTROL_ARMADO_ANDROID")
if (afuera != null) {
    allprojects { layout.buildDirectory.set(file("$afuera/${project.name}")) }
}
