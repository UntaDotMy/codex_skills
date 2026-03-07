# Mobile Platform-Specific APIs

## iOS Platform APIs

### Permissions

**Location Services:**
```swift
import CoreLocation

class LocationManager: NSObject, CLLocationManagerDelegate {
    let manager = CLLocationManager()

    func requestLocationPermission() {
        // Request when-in-use authorization
        manager.requestWhenInUseAuthorization()

        // Or request always authorization
        // manager.requestAlwaysAuthorization()
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        switch manager.authorizationStatus {
        case .notDetermined:
            // User hasn't decided yet
        case .restricted, .denied:
            // Permission denied
        case .authorizedWhenInUse, .authorizedAlways:
            // Permission granted
            manager.startUpdatingLocation()
        @unknown default:
            break
        }
    }
}
```

**Info.plist entries required:**
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>We need your location to show nearby places</string>
<key>NSLocationAlwaysUsageDescription</key>
<string>We need your location to track your route</string>
```

**Camera & Photos:**
```swift
import AVFoundation
import Photos

// Camera permission
AVCaptureDevice.requestAccess(for: .video) { granted in
    if granted {
        // Camera access granted
    }
}

// Photo library permission
PHPhotoLibrary.requestAuthorization { status in
    switch status {
    case .authorized:
        // Access granted
    case .denied, .restricted:
        // Access denied
    case .notDetermined:
        // Not asked yet
    @unknown default:
        break
    }
}
```

**Info.plist entries:**
```xml
<key>NSCameraUsageDescription</key>
<string>We need camera access to take photos</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>We need photo access to select images</string>
```

**Notifications:**
```swift
import UserNotifications

UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
    if granted {
        DispatchQueue.main.async {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
}
```

### Background Tasks

**Background Fetch:**
```swift
import BackgroundTasks

// Register task
BGTaskScheduler.shared.register(
    forTaskWithIdentifier: "com.app.refresh",
    using: nil
) { task in
    self.handleAppRefresh(task: task as! BGAppRefreshTask)
}

// Schedule task
func scheduleAppRefresh() {
    let request = BGAppRefreshTaskRequest(identifier: "com.app.refresh")
    request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60) // 15 minutes

    try? BGTaskScheduler.shared.submit(request)
}

// Handle task
func handleAppRefresh(task: BGAppRefreshTask) {
    scheduleAppRefresh() // Schedule next refresh

    task.expirationHandler = {
        // Clean up
    }

    // Do work
    fetchData { success in
        task.setTaskCompleted(success: success)
    }
}
```

**Info.plist:**
```xml
<key>BGTaskSchedulerPermittedIdentifiers</key>
<array>
    <string>com.app.refresh</string>
</array>
```

### Lifecycle

**App Lifecycle (SwiftUI):**
```swift
@main
struct MyApp: App {
    @Environment(\.scenePhase) var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .onChange(of: scenePhase) { phase in
            switch phase {
            case .active:
                // App is active
            case .inactive:
                // App is inactive (transitioning)
            case .background:
                // App is in background
            @unknown default:
                break
            }
        }
    }
}
```

**App Lifecycle (UIKit):**
```swift
class AppDelegate: UIResponder, UIApplicationDelegate {
    func applicationDidEnterBackground(_ application: UIApplication) {
        // Save state
    }

    func applicationWillEnterForeground(_ application: UIApplication) {
        // Restore state
    }

    func applicationWillTerminate(_ application: UIApplication) {
        // Final cleanup
    }
}
```

### Local Notifications

```swift
import UserNotifications

// Schedule notification
let content = UNMutableNotificationContent()
content.title = "Reminder"
content.body = "Don't forget to check in"
content.sound = .default

let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 60, repeats: false)
let request = UNNotificationRequest(identifier: "reminder", content: content, trigger: trigger)

UNUserNotificationCenter.current().add(request) { error in
    if let error = error {
        print("Error: \(error)")
    }
}
```

---

## Android Platform APIs

### Permissions

**Runtime Permissions (Android 6.0+):**
```kotlin
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {
    private val LOCATION_PERMISSION_CODE = 100

    fun requestLocationPermission() {
        when {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED -> {
                // Permission already granted
                startLocationUpdates()
            }
            shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_FINE_LOCATION) -> {
                // Show explanation why permission is needed
                showPermissionRationale()
            }
            else -> {
                // Request permission
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.ACCESS_FINE_LOCATION),
                    LOCATION_PERMISSION_CODE
                )
            }
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            LOCATION_PERMISSION_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    startLocationUpdates()
                } else {
                    // Permission denied
                }
            }
        }
    }
}
```

**AndroidManifest.xml:**
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

### Background Work (WorkManager)

```kotlin
import androidx.work.*
import java.util.concurrent.TimeUnit

class SyncWorker(context: Context, params: WorkerParameters) : Worker(context, params) {
    override fun doWork(): Result {
        return try {
            // Do background work
            syncData()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}

// Schedule work
fun scheduleSync() {
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .setRequiresBatteryNotLow(true)
        .build()

    val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
        15, TimeUnit.MINUTES
    )
        .setConstraints(constraints)
        .build()

    WorkManager.getInstance(context).enqueueUniquePeriodicWork(
        "sync",
        ExistingPeriodicWorkPolicy.KEEP,
        syncRequest
    )
}
```

### Lifecycle

**Activity Lifecycle:**
```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Initialize UI
    }

    override fun onStart() {
        super.onStart()
        // Activity visible
    }

    override fun onResume() {
        super.onResume()
        // Activity interactive
    }

    override fun onPause() {
        super.onPause()
        // Activity losing focus
    }

    override fun onStop() {
        super.onStop()
        // Activity no longer visible
    }

    override fun onDestroy() {
        super.onDestroy()
        // Activity being destroyed
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        // Save state
        outState.putString("key", "value")
    }

    override fun onRestoreInstanceState(savedInstanceState: Bundle) {
        super.onRestoreInstanceState(savedInstanceState)
        // Restore state
        val value = savedInstanceState.getString("key")
    }
}
```

**Jetpack Compose Lifecycle:**
```kotlin
@Composable
fun MyScreen() {
    val lifecycleOwner = LocalLifecycleOwner.current

    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> {
                    // Screen resumed
                }
                Lifecycle.Event.ON_PAUSE -> {
                    // Screen paused
                }
                else -> {}
            }
        }

        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }
}
```

### Notifications

```kotlin
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.core.app.NotificationCompat

fun createNotificationChannel(context: Context) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        val channel = NotificationChannel(
            "channel_id",
            "Channel Name",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Channel Description"
        }

        val notificationManager = context.getSystemService(NotificationManager::class.java)
        notificationManager.createNotificationChannel(channel)
    }
}

fun showNotification(context: Context) {
    val notification = NotificationCompat.Builder(context, "channel_id")
        .setSmallIcon(R.drawable.ic_notification)
        .setContentTitle("Title")
        .setContentText("Message")
        .setPriority(NotificationCompat.PRIORITY_DEFAULT)
        .build()

    val notificationManager = context.getSystemService(NotificationManager::class.java)
    notificationManager.notify(1, notification)
}
```

---

## Platform Differences & Common Pitfalls

### Permission Handling

**iOS:**
- Permissions requested at runtime
- User can change permissions in Settings
- App doesn't know if permission was denied or not determined (privacy)
- Must provide usage descriptions in Info.plist

**Android:**
- Permissions declared in manifest
- Runtime permissions required for dangerous permissions (Android 6.0+)
- Can check if permission was permanently denied
- Should show rationale before requesting

**Common Pitfall:** Not handling permission denial gracefully

**Solution:** Always provide fallback functionality or clear explanation

### Background Execution

**iOS:**
- Very restrictive background execution
- Background tasks have time limits (~30 seconds)
- Must use specific background modes (location, audio, etc.)
- Background fetch is opportunistic (system decides when to run)

**Android:**
- More flexible background execution
- WorkManager for deferrable work
- Foreground services for user-visible work
- Doze mode and App Standby restrict background

**Common Pitfall:** Assuming background tasks run immediately

**Solution:** Use appropriate APIs (WorkManager, BackgroundTasks) and handle delays

### Lifecycle Management

**iOS:**
- App can be terminated at any time in background
- Must save state in `applicationDidEnterBackground`
- State restoration API for UI state

**Android:**
- Activity can be destroyed and recreated
- Must save state in `onSaveInstanceState`
- ViewModel survives configuration changes

**Common Pitfall:** Not saving/restoring state properly

**Solution:** Always save critical state, test by killing app in background

### Push Notifications

**iOS (APNs):**
- Requires Apple Developer account
- Device token required
- Silent notifications limited

**Android (FCM):**
- Free, no account required
- Registration token required
- More flexible notification options

**Common Pitfall:** Not handling token refresh

**Solution:** Listen for token updates and update server

### File Storage

**iOS:**
- Sandboxed file system
- Documents directory for user files
- Caches directory for temporary files
- iCloud sync available

**Android:**
- Scoped storage (Android 10+)
- Internal storage (private to app)
- External storage (shared, requires permission)
- MediaStore for media files

**Common Pitfall:** Storing files in wrong location

**Solution:** Use appropriate directory for file type

---

## Code Examples for Common Tasks

### Checking Network Connectivity

**iOS:**
```swift
import Network

let monitor = NWPathMonitor()
monitor.pathUpdateHandler = { path in
    if path.status == .satisfied {
        // Connected
    } else {
        // Disconnected
    }
}
monitor.start(queue: DispatchQueue.global())
```

**Android:**
```kotlin
import android.net.ConnectivityManager
import android.net.NetworkCapabilities

fun isNetworkAvailable(context: Context): Boolean {
    val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    val network = connectivityManager.activeNetwork ?: return false
    val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false

    return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
}
```

### Biometric Authentication

**iOS:**
```swift
import LocalAuthentication

func authenticateWithBiometrics() {
    let context = LAContext()
    var error: NSError?

    if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
        context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: "Authenticate to access") { success, error in
            if success {
                // Authenticated
            }
        }
    }
}
```

**Android:**
```kotlin
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat

fun authenticateWithBiometrics(activity: FragmentActivity) {
    val executor = ContextCompat.getMainExecutor(activity)
    val biometricPrompt = BiometricPrompt(activity, executor, object : BiometricPrompt.AuthenticationCallback() {
        override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
            // Authenticated
        }

        override fun onAuthenticationFailed() {
            // Failed
        }
    })

    val promptInfo = BiometricPrompt.PromptInfo.Builder()
        .setTitle("Biometric Authentication")
        .setSubtitle("Authenticate to access")
        .setNegativeButtonText("Cancel")
        .build()

    biometricPrompt.authenticate(promptInfo)
}
```

---

## Best Practices

1. **Request permissions contextually** - Ask when feature is used, not on app launch
2. **Provide clear rationale** - Explain why permission is needed
3. **Handle denial gracefully** - Provide fallback or guide to settings
4. **Save state frequently** - App can be killed at any time
5. **Test background scenarios** - Kill app, low memory, airplane mode
6. **Respect battery** - Minimize background work, use appropriate APIs
7. **Follow platform guidelines** - iOS HIG, Material Design
8. **Test on real devices** - Simulators don't catch everything
9. **Handle process death** - Test by enabling "Don't keep activities" (Android)
10. **Monitor API changes** - Platform APIs evolve, stay updated

## Resources

- [iOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Android Developer Guides](https://developer.android.com/guide)
- [iOS App Programming Guide](https://developer.apple.com/library/archive/documentation/iPhone/Conceptual/iPhoneOSProgrammingGuide/)
- [Android App Architecture](https://developer.android.com/topic/architecture)
