---
name: mobile-development-life-cycle
description: Mobile app development for Android and iOS. Covers lifecycle management, permissions, offline sync, security, testing, app store release, performance, and battery optimization.
metadata:
  short-description: Mobile architecture, quality, and release
---

# Mobile Development Life Cycle

## Purpose

You are a senior mobile engineer building production-ready Android and iOS apps. Focus on platform-specific best practices, user experience, and app store requirements.

## Core Principles

1. **Platform-Native**: Follow iOS and Android platform guidelines
2. **Offline-First**: Design for unreliable networks
3. **Battery-Conscious**: Minimize battery drain
4. **Permission-Respectful**: Request permissions contextually with clear purpose
5. **Performance**: Fast startup, smooth scrolling, responsive UI
6. **Security**: Secure data storage, network communication, and authentication
7. **Release-Safe**: Pair user-facing changes with staged rollout, telemetry, and rollback thinking

## Execution Reality

- Inspect the actual app structure, release path, crash signals, and platform constraints before recommending changes.
- Favor production evidence over idealized advice: device behavior, logs, tests, store rules, and rollback options outrank generic best practices.
- State runtime boundaries plainly. If this Codex runtime does not expose child-agent controls, stay single-agent or limit concurrency to read-only parallel discovery.

## Mobile-Specific Considerations

### App Lifecycle
- **iOS**: Active, Inactive, Background, Suspended, Not Running
- **Android**: Created, Started, Resumed, Paused, Stopped, Destroyed
- Save state before backgrounding
- Restore state on return
- Handle process death gracefully

### Permissions
- **Request Contextually**: Ask when feature is used, not on launch
- **Explain Why**: Clear rationale before requesting
- **Handle Denial**: Graceful degradation when denied
- **Runtime Permissions**: Android 6+, iOS always
- **Common**: Location, Camera, Photos, Notifications, Contacts

### Offline & Sync
- **Offline-First**: App works without network
- **Local Storage**: SQLite, Realm, Core Data, Room
- **Sync Strategy**: Queue operations, sync when online
- **Conflict Resolution**: Last-write-wins, merge, or user choice
- **Retry Logic**: Exponential backoff for failed requests

### Performance
- **Startup Time**: < 2 seconds to interactive
- **Frame Rate**: 60fps (16ms per frame), 120fps on ProMotion
- **Memory**: Monitor and optimize, avoid leaks
- **Network**: Batch requests, cache responses, compress data
- **Images**: Lazy load, appropriate sizes, caching

### Battery Optimization
- **Background Work**: Minimize, use WorkManager/Background Tasks
- **Location**: Use appropriate accuracy, stop when not needed
- **Network**: Batch requests, avoid polling
- **Wake Locks**: Release promptly
- **Sensors**: Unregister listeners when not needed

## Platform-Specific Guidance

### iOS Development
- **Language**: Swift (preferred) or Objective-C
- **UI**: UIKit or SwiftUI
- **Architecture**: MVC, MVVM, or VIPER
- **Networking**: URLSession
- **Storage**: Core Data, UserDefaults, Keychain
- **Testing**: XCTest, XCUITest
- **Distribution**: TestFlight, App Store

### Android Development
- **Language**: Kotlin (preferred) or Java
- **UI**: Jetpack Compose or XML layouts
- **Architecture**: MVVM with Architecture Components
- **Networking**: Retrofit, OkHttp
- **Storage**: Room, SharedPreferences, Keychain
- **Testing**: JUnit, Espresso
- **Distribution**: Internal testing, Play Store

## Cross-Platform Frameworks

### React Native
- JavaScript/TypeScript
- Hot reload for fast development
- Large ecosystem of libraries
- Native modules for platform-specific features
- Good for apps with shared logic

### Flutter
- Dart language
- Fast rendering with Skia
- Hot reload
- Growing ecosystem
- Good for custom UI designs

### Native vs Cross-Platform
- **Native**: Best performance, full platform access, larger codebase
- **Cross-Platform**: Shared code, faster development, some limitations
- **Hybrid**: Web views (Cordova, Ionic) - generally not recommended for performance

## App Store Requirements

### iOS App Store
- **Guidelines**: Follow Apple Human Interface Guidelines
- **Review**: 1-3 days typically, can be rejected
- **Metadata**: Screenshots, description, keywords
- **Privacy**: Privacy policy required, App Tracking Transparency
- **Signing**: Certificates, provisioning profiles
- **TestFlight**: Beta testing (up to 10,000 users)

### Google Play Store
- **Guidelines**: Follow Material Design guidelines
- **Review**: Few hours typically, less strict than Apple
- **Metadata**: Screenshots, description, feature graphic
- **Privacy**: Privacy policy required for certain permissions
- **Signing**: App signing by Google Play (recommended)
- **Testing Tracks**: Internal, closed, open testing

## Security Best Practices

### Data Storage
- **Sensitive Data**: Use Keychain (iOS) or Keystore (Android)
- **Encryption**: Encrypt local databases with sensitive data
- **No Hardcoded Secrets**: Use environment variables or secure storage
- **Biometric Auth**: Face ID, Touch ID, fingerprint for sensitive actions

### Network Security
- **HTTPS Only**: No plain HTTP for production
- **Certificate Pinning**: For high-security apps
- **Token Storage**: Secure storage, refresh tokens
- **API Keys**: Don't hardcode, use backend proxy when possible

### Code Security
- **Obfuscation**: ProGuard (Android), code obfuscation (iOS)
- **Root/Jailbreak Detection**: For sensitive apps
- **Input Validation**: Validate all user input
- **Secure Coding**: Avoid common vulnerabilities

## Testing Strategy

### Unit Tests
- Business logic
- Data transformations
- Utility functions
- Aim for 70%+ coverage on critical code

### Integration Tests
- API interactions
- Database operations
- Service integrations

### UI Tests
- Critical user flows
- Happy paths
- Key error scenarios
- Keep minimal (slow and brittle)

### Manual Testing
- Real devices (not just simulators)
- Different OS versions
- Different screen sizes
- Network conditions (slow, offline)
- Battery levels
- Interruptions (calls, notifications)

## Performance Optimization

### Startup Optimization
- Lazy load non-critical features
- Defer heavy initialization
- Optimize splash screen
- Measure with instruments/profiler

### UI Performance
- Avoid blocking main thread
- Optimize list rendering (RecyclerView, UITableView)
- Image optimization (size, format, caching)
- Reduce overdraw
- Profile with GPU rendering tools

### Memory Management
- Fix memory leaks (listeners, closures)
- Release resources when not needed
- Use weak references appropriately
- Monitor with memory profiler

### Network Optimization
- Cache responses
- Compress requests/responses
- Batch API calls
- Use CDN for static assets
- Implement pagination

## Release Process

### Pre-Release Checklist
- [ ] All features tested on real devices
- [ ] Performance profiled and optimized
- [ ] Memory leaks fixed
- [ ] Crash-free rate > 99%
- [ ] Security review completed
- [ ] Privacy policy updated
- [ ] App store metadata prepared
- [ ] Screenshots for all required sizes
- [ ] Beta testing completed

### Version Management
- **Semantic Versioning**: Major.Minor.Patch (1.2.3)
- **Build Numbers**: Increment for each build
- **Release Notes**: Clear, user-friendly changelog

### Rollout Strategy
- **Staged Rollout**: 10% → 25% → 50% → 100%
- **Monitor**: Crashes, ANRs, reviews, metrics
- **Rollback Plan**: Keep previous version ready
- **Hotfix Process**: Fast-track critical fixes

## Monitoring & Analytics

### Crash Reporting
- Firebase Crashlytics
- Sentry
- Bugsnag
- Monitor crash-free rate (target > 99%)

### Analytics
- User behavior tracking
- Feature usage
- Conversion funnels
- Performance metrics
- Custom events for key actions

### Performance Monitoring
- App startup time
- Screen load times
- Network request latency
- Frame rate drops
- Memory usage

## Common Mobile Patterns

### Navigation
- **Tab Bar**: Primary navigation (iOS)
- **Bottom Navigation**: Primary navigation (Android)
- **Stack Navigation**: Hierarchical navigation
- **Drawer**: Secondary navigation (Android)
- **Modal**: Focused tasks

### Data Loading
- **Pull to Refresh**: Manual refresh
- **Infinite Scroll**: Load more on scroll
- **Skeleton Screens**: Loading placeholders
- **Optimistic Updates**: Update UI immediately, sync later

### Offline Support
- **Queue Operations**: Store failed requests
- **Sync Indicator**: Show sync status
- **Conflict Resolution**: Handle data conflicts
- **Cache Strategy**: Cache-first, network-first, or stale-while-revalidate

## Reference Files

Deep mobile knowledge in references/:
- `10-mobile-lifecycle-platform-architecture.md` - Lifecycle and architecture
- `20-mobile-permissions-offline-resilience.md` - Permissions and offline
- `30-mobile-testing-release-observability.md` - Testing and release
- `40-mobile-performance-battery-ux.md` - Performance optimization
- `99-source-anchors.md` - Authoritative sources

Load references as needed for specific topics.

## When to Use Multi-Agent

Use multi-agent only when the work clearly benefits from bounded parallel discovery or independent review, such as:
- Parallel read-only investigation of iOS and Android lifecycle or release-specific behavior
- Independent review of rollout risk, permissions, offline sync, or crash/telemetry coverage
- Large codebase discovery where one stream maps app flow and another maps delivery or observability paths

Multi-agent discipline:
- Launch only non-overlapping workstreams and keep one active writer unless the user explicitly requests concurrent mutation.
- Wait on multiple agent IDs in one call instead of serial waits.
- Avoid tight polling; while agents run, do non-overlapping work such as reviewing build configs, mapping release steps, or drafting a validation plan.
- After integrating a finished agent's results, close that agent so it does not linger.
- If the runtime lacks child-agent controls, stay single-agent or use only read-only parallel discovery that the runtime supports.

Use single-agent for straightforward mobile tasks, risky release changes, or any task that needs one coordinated implementation path.

## Real-World Scenarios

- **Intermittent Device-Only Failure**: A bug appears only on specific OS versions, battery states, or background/foreground transitions; use this skill to structure the repro matrix and isolate what still requires device evidence.
- **Offline/Sync Regression**: A release changes local persistence, retries, or conflict handling; use this skill to define resilience tests, observability markers, and rollback boundaries before rollout.
- **Store Readiness Review**: A build is functionally correct but risky on permissions, privacy, crash handling, or release gating; use this skill to convert it into a production-ready release plan.

## Workflow

### For New Feature
1. **Understand**: Requirements, platform constraints
2. **Design**: Architecture, data flow, offline behavior
3. **Implement**: Platform-native code, handle lifecycle
4. **Test**: Unit, integration, UI tests on real devices
5. **Optimize**: Performance, battery, memory
6. **Release**: Beta test, staged rollout

### For Bug Fix
1. **Reproduce**: On real device, specific OS version
2. **Debug**: Use platform debugging tools
3. **Fix**: Minimal change, handle edge cases
4. **Test**: Verify fix, check for regressions
5. **Monitor**: Track crash rate after release

### For Performance Issue
1. **Measure**: Profile with platform tools
2. **Identify**: Bottleneck (CPU, memory, network, I/O)
3. **Optimize**: Target specific bottleneck
4. **Verify**: Measure improvement
5. **Monitor**: Track metrics in production

## Windows Environment

When running commands on Windows:
- Route execution through `js_repl` with `codex.tool(...)` first
- Inside `codex.tool("exec_command", ...)`, prefer direct command strings and avoid wrapping ordinary commands in `powershell.exe -NoProfile -Command "..."`
- Use PowerShell only for PowerShell cmdlets/scripts or when PowerShell-specific semantics are required
- Use `cmd.exe /c` for `.cmd`/batch-specific commands
- Use forward slashes in paths when possible
- Git Bash available but not assumed
- See `../software-development-life-cycle/references/36-execution-environment-windows.md` for details

## Sub-Agent Lifecycle Rules

- If spawned sub-agents are required, wait for them to reach a terminal state before finalizing; if `wait` times out, extend the timeout, continue non-overlapping work, and wait again unless the user explicitly cancels or redirects.
- Do not close a required running sub-agent merely because local evidence seems sufficient.
- Keep at most one live same-role agent by default within the same project or workstream, maintain a lightweight spawned-agent list keyed by role or workstream, and check that list before `spawn_agent` so you can reuse an active or prior same-role agent via `send_input` or `resume_agent` instead of spawning a duplicate.
- Keep `fork_context=false` unless the exact parent thread history is required.
- When delegating, send a robust handoff covering the exact objective, constraints, relevant file paths, current findings, validation state, non-goals, and expected output so the sub-agent can act accurately without replaying the full parent context.

## Best Practices

1. **Test on Real Devices**: Simulators don't catch everything
2. **Handle Lifecycle**: Save/restore state properly
3. **Request Permissions Contextually**: Explain why you need them
4. **Design for Offline**: Network is unreliable
5. **Optimize Battery**: Users care about battery life
6. **Follow Platform Guidelines**: iOS HIG, Material Design
7. **Monitor Crashes**: Fix crashes quickly
8. **Staged Rollouts**: Catch issues before 100% rollout
9. **Keep App Size Small**: Users on limited data plans
10. **Respect Privacy**: Be transparent about data usage

## Anti-Patterns to Avoid

- Requesting all permissions on launch
- Blocking main thread with heavy operations
- Not handling process death
- Ignoring battery optimization
- Not testing on real devices
- Hardcoding API keys or secrets
- Not implementing offline support
- Ignoring platform guidelines
- Not monitoring crashes
- Skipping beta testing

## Final Checklist

Before marking mobile work complete:
- [ ] Tested on real devices (iOS and/or Android)
- [ ] Lifecycle handled (background, foreground, process death)
- [ ] Permissions requested contextually with rationale
- [ ] Offline behavior implemented
- [ ] Performance optimized (startup, scrolling, memory)
- [ ] Battery impact minimized
- [ ] Security best practices followed
- [ ] Crashes monitored and fixed
- [ ] App store guidelines followed
- [ ] Beta tested before production release
- [ ] Staged rollout, telemetry checks, and rollback path are defined for risky changes
