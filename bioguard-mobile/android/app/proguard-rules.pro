# Flutter specific rules
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

# BioGuard Security Module
-keep class com.bioguard.nexus.** { *; }

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}
