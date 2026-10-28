# ProGuard / R8 Rules for RubberGuard AI

# Keep TensorFlow Lite and native JNI bindings
-keep class org.tensorflow.lite.** { *; }
-dontwarn org.tensorflow.lite.**

# Keep OpenCV native methods and core classes
-keep class org.opencv.** { *; }
-dontwarn org.opencv.**

# Keep Room database schemas and entities
-keep class androidx.room.** { *; }
-keep class * extends androidx.room.RoomDatabase
-keep class com.rubber.disease.data.** { *; }
-dontwarn androidx.room.**

# Keep ML and prediction data models
-keep class com.rubber.disease.ml.** { *; }
-keep class com.rubber.disease.viewmodels.** { *; }

# Keep ViewBinding generated classes
-keep class com.rubber.disease.databinding.** { *; }
