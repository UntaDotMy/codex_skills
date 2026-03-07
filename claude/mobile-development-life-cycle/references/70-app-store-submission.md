# App Store Submission Guide

## iOS App Store Submission

### Pre-Submission Requirements

**1. Apple Developer Account**
- Individual: $99/year
- Organization: $99/year
- Enterprise: $299/year (for internal distribution only)

**2. App Store Connect Setup**
- Create app record
- Fill in app information
- Set up pricing and availability
- Configure App Store listing

**3. Certificates & Provisioning**
- Distribution certificate
- App Store provisioning profile
- Push notification certificate (if using push)

### App Store Guidelines Compliance

**Must Follow:**

1. **Safety**
   - No objectionable content
   - No user-generated content without moderation
   - No encouragement of illegal activity
   - Child safety (COPPA compliance if targeting children)

2. **Performance**
   - App must be complete and functional
   - No placeholder content
   - No crashes or bugs
   - Fast loading times

3. **Business**
   - Clear pricing
   - In-app purchases must use Apple's system
   - Subscriptions must provide value
   - No misleading users

4. **Design**
   - Follow Human Interface Guidelines
   - Native iOS look and feel
   - Proper use of system features
   - Accessible to users with disabilities

5. **Legal**
   - Privacy policy required
   - Terms of service (if applicable)
   - Proper use of trademarks
   - Age rating accuracy

### Required Assets

**App Icons:**
- 1024x1024px (App Store)
- Various sizes for device (handled by Xcode)

**Screenshots:**
- iPhone 6.7" (required)
- iPhone 6.5" (required)
- iPhone 5.5" (optional)
- iPad Pro 12.9" (if iPad app)
- iPad Pro 11" (if iPad app)

**App Preview Videos (Optional):**
- 15-30 seconds
- Portrait and landscape
- Show actual app functionality

### Info.plist Requirements

**Privacy Permissions:**
```xml
<!-- Camera -->
<key>NSCameraUsageDescription</key>
<string>We need camera access to take photos</string>

<!-- Photo Library -->
<key>NSPhotoLibraryUsageDescription</key>
<string>We need photo access to select images</string>

<!-- Location -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>We need your location to show nearby places</string>

<!-- Microphone -->
<key>NSMicrophoneUsageDescription</key>
<string>We need microphone access to record audio</string>

<!-- Contacts -->
<key>NSContactsUsageDescription</key>
<string>We need contacts access to find friends</string>
```

**App Transport Security:**
```xml
<!-- Allow HTTP (not recommended for production) -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
</dict>
```

### Submission Process

**1. Archive Build**
```bash
# Using Xcode
Product > Archive

# Using Fastlane
fastlane build
```

**2. Upload to App Store Connect**
```bash
# Using Xcode Organizer
Window > Organizer > Distribute App

# Using Fastlane
fastlane upload_to_app_store
```

**3. Fill App Information**
- App name (30 characters max)
- Subtitle (30 characters max)
- Description (4000 characters max)
- Keywords (100 characters max, comma-separated)
- Support URL
- Marketing URL (optional)
- Privacy policy URL

**4. Set Pricing & Availability**
- Price tier
- Available territories
- Release date (manual or automatic)

**5. Submit for Review**
- Select build
- Add release notes
- Submit

### Review Process

**Timeline:**
- Typical: 24-48 hours
- Can be longer during holidays
- Expedited review available (limited use)

**Common Rejection Reasons:**

1. **Crashes/Bugs**
   - App crashes on launch
   - Features don't work
   - Broken links

2. **Incomplete Information**
   - Missing privacy policy
   - Incomplete app description
   - Missing demo account (if required)

3. **Design Issues**
   - Doesn't follow HIG
   - Poor user experience
   - Placeholder content

4. **Guideline Violations**
   - Spam/copycat apps
   - Misleading functionality
   - Inappropriate content

5. **Performance Issues**
   - Slow loading
   - Excessive battery drain
   - Large app size without justification

### TestFlight (Beta Testing)

**Internal Testing:**
- Up to 100 internal testers
- No review required
- Instant distribution

**External Testing:**
- Up to 10,000 external testers
- Requires beta review (faster than App Store review)
- Public link or email invites

**Setup:**
```bash
# Upload build
fastlane beta

# Or via Xcode
Product > Archive > Distribute App > TestFlight
```

---

## Google Play Store Submission

### Pre-Submission Requirements

**1. Google Play Console Account**
- One-time fee: $25
- Organization verification (if applicable)

**2. App Signing**
- Google Play App Signing (recommended)
- Upload key and app signing key
- Keep keystore safe (cannot be recovered)

**3. Play Console Setup**
- Create app
- Fill in store listing
- Set up pricing and distribution
- Configure content rating

### Play Store Policies Compliance

**Must Follow:**

1. **Content Policy**
   - No illegal content
   - No hate speech
   - No violence or dangerous content
   - No sexual content

2. **Privacy & Security**
   - Privacy policy required
   - Data safety form required
   - Proper permission usage
   - Secure data transmission

3. **Monetization**
   - Clear pricing
   - In-app purchases properly disclosed
   - Subscriptions must provide value

4. **User Experience**
   - App must be stable
   - No deceptive behavior
   - Proper use of permissions
   - Accessible features

### Required Assets

**App Icon:**
- 512x512px (high-res icon)
- 192x192px (app icon)

**Feature Graphic:**
- 1024x500px (required)

**Screenshots:**
- Phone: 2-8 screenshots (minimum 320px)
- 7-inch tablet: 2-8 screenshots (optional)
- 10-inch tablet: 2-8 screenshots (optional)

**Promo Video (Optional):**
- YouTube video link

### AndroidManifest.xml Requirements

**Permissions:**
```xml
<!-- Only request permissions you actually use -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

<!-- Declare features -->
<uses-feature android:name="android.hardware.camera" android:required="false" />
<uses-feature android:name="android.hardware.location.gps" android:required="false" />
```

**Version Info:**
```xml
<manifest
    android:versionCode="1"
    android:versionName="1.0.0">
```

### Build Configuration

**build.gradle (app):**
```gradle
android {
    defaultConfig {
        applicationId "com.example.app"
        minSdkVersion 24
        targetSdkVersion 34
        versionCode 1
        versionName "1.0.0"
    }

    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
            signingConfig signingConfigs.release
        }
    }

    signingConfigs {
        release {
            storeFile file("keystore.jks")
            storePassword System.getenv("KEYSTORE_PASSWORD")
            keyAlias System.getenv("KEY_ALIAS")
            keyPassword System.getenv("KEY_PASSWORD")
        }
    }
}
```

### Submission Process

**1. Build Release APK/AAB**
```bash
# Build AAB (recommended)
./gradlew bundleRelease

# Build APK
./gradlew assembleRelease
```

**2. Upload to Play Console**
- Go to Release > Production
- Create new release
- Upload AAB/APK
- Add release notes

**3. Fill Store Listing**
- App name (50 characters max)
- Short description (80 characters max)
- Full description (4000 characters max)
- App icon and screenshots
- Feature graphic
- Category
- Contact details

**4. Content Rating**
- Complete questionnaire
- Get rating (Everyone, Teen, Mature, etc.)

**5. Data Safety**
- Declare data collection
- Explain data usage
- Security practices

**6. Pricing & Distribution**
- Free or paid
- Available countries
- Content rating
- Target audience

**7. Submit for Review**
- Review and publish

### Review Process

**Timeline:**
- Typical: Few hours to 1-2 days
- Faster than iOS App Store
- Can be longer for first submission

**Common Rejection Reasons:**

1. **Policy Violations**
   - Misleading content
   - Inappropriate content
   - Spam

2. **Technical Issues**
   - Crashes
   - Broken functionality
   - Security vulnerabilities

3. **Metadata Issues**
   - Misleading description
   - Inappropriate screenshots
   - Keyword stuffing

4. **Privacy Issues**
   - Missing privacy policy
   - Incorrect data safety form
   - Improper permission usage

### Testing Tracks

**Internal Testing:**
- Up to 100 testers
- Instant distribution
- No review required

**Closed Testing:**
- Up to 100 lists of testers
- Email invites
- Faster review

**Open Testing:**
- Public link
- Anyone can join
- Requires review

**Production:**
- Public release
- Full review process

---

## Pre-Submission Checklist

### Both Platforms

**Functionality:**
- [ ] App launches without crashes
- [ ] All features work as expected
- [ ] No placeholder content
- [ ] Proper error handling
- [ ] Offline functionality (if applicable)
- [ ] Network error handling

**Performance:**
- [ ] Fast startup (< 2 seconds)
- [ ] Smooth scrolling (60fps)
- [ ] No memory leaks
- [ ] Reasonable battery usage
- [ ] Optimized images and assets

**Security:**
- [ ] HTTPS for all network requests
- [ ] No hardcoded secrets
- [ ] Proper authentication
- [ ] Secure data storage
- [ ] Input validation

**Privacy:**
- [ ] Privacy policy published
- [ ] Permissions requested contextually
- [ ] Clear permission rationale
- [ ] Data collection disclosed
- [ ] GDPR/CCPA compliance (if applicable)

**Testing:**
- [ ] Tested on real devices
- [ ] Tested on different OS versions
- [ ] Tested offline
- [ ] Tested with poor network
- [ ] Tested interruptions
- [ ] Crash-free rate > 99%

**Assets:**
- [ ] App icon (all sizes)
- [ ] Screenshots (all required sizes)
- [ ] Feature graphic (Android)
- [ ] App description
- [ ] Keywords/tags
- [ ] Release notes

**Legal:**
- [ ] Privacy policy URL
- [ ] Terms of service (if applicable)
- [ ] Age rating accurate
- [ ] Content rating completed
- [ ] Proper licensing for third-party content

### iOS Specific

- [ ] Follows Human Interface Guidelines
- [ ] All required Info.plist entries
- [ ] TestFlight tested
- [ ] Proper use of Apple services
- [ ] App Store Connect information complete

### Android Specific

- [ ] Follows Material Design guidelines
- [ ] ProGuard/R8 enabled
- [ ] App signing configured
- [ ] Data safety form completed
- [ ] Target latest Android API level

---

## Post-Submission

### Monitoring

**Track Metrics:**
- Downloads/installs
- Crash-free rate
- User ratings and reviews
- Retention rate
- Active users

**Tools:**
- App Store Connect Analytics (iOS)
- Google Play Console (Android)
- Firebase Analytics
- Crashlytics

### Responding to Reviews

**Best Practices:**
- Respond to negative reviews professionally
- Thank users for positive reviews
- Address bugs mentioned in reviews
- Don't argue with users
- Provide support contact

### Updates

**When to Update:**
- Bug fixes (ASAP)
- New features (planned releases)
- OS compatibility (when new OS releases)
- Security patches (immediately)

**Update Process:**
- Increment version number
- Write clear release notes
- Test thoroughly
- Submit for review

---

## Common Mistakes to Avoid

1. **Not testing on real devices** - Simulators miss issues
2. **Missing privacy policy** - Required for both stores
3. **Requesting unnecessary permissions** - Users will deny
4. **Poor app description** - Users won't understand your app
5. **Low-quality screenshots** - First impression matters
6. **Not responding to reviews** - Shows you don't care
7. **Ignoring crashes** - Users will uninstall
8. **Not updating regularly** - App becomes stale
9. **Violating guidelines** - App gets rejected or removed
10. **Not monitoring metrics** - Can't improve what you don't measure

---

## Resources

### iOS
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [App Store Connect Help](https://developer.apple.com/help/app-store-connect/)
- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [TestFlight Documentation](https://developer.apple.com/testflight/)

### Android
- [Google Play Policy Center](https://play.google.com/about/developer-content-policy/)
- [Play Console Help](https://support.google.com/googleplay/android-developer/)
- [Material Design Guidelines](https://material.io/design)
- [Android App Bundle](https://developer.android.com/guide/app-bundle)
