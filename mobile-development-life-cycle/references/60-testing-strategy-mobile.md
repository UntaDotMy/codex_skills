# Mobile Testing Strategy

## Testing Pyramid for Mobile

```
        /\
       /E2E\
      /------\
     /Integration\
    /--------------\
   /   Unit Tests   \
  /------------------\
```

**Ratio:** 70% Unit, 20% Integration, 10% E2E/UI

## Unit Testing

### What to Test

**Business Logic:**
- ViewModels (Android) / View logic (iOS)
- Data transformations
- Validation logic
- Use cases / Interactors
- Utility functions

**Data Layer:**
- Repository implementations
- Data source logic
- API response parsing
- Database operations (with in-memory DB)

### iOS Unit Testing (XCTest)

**Testing a ViewModel:**
```swift
import XCTest
@testable import MyApp

class LoginViewModelTests: XCTestCase {
    var viewModel: LoginViewModel!
    var mockAuthService: MockAuthService!

    override func setUp() {
        super.setUp()
        mockAuthService = MockAuthService()
        viewModel = LoginViewModel(authService: mockAuthService)
    }

    override func tearDown() {
        viewModel = nil
        mockAuthService = nil
        super.tearDown()
    }

    func testLoginSuccess() {
        // Arrange
        let email = "test@example.com"
        let password = "password123"
        mockAuthService.shouldSucceed = true

        let expectation = self.expectation(description: "Login completes")

        // Act
        viewModel.login(email: email, password: password) { result in
            // Assert
            switch result {
            case .success:
                XCTAssertTrue(self.viewModel.isLoggedIn)
                expectation.fulfill()
            case .failure:
                XCTFail("Expected success")
            }
        }

        waitForExpectations(timeout: 1.0)
    }

    func testLoginFailure() {
        // Arrange
        mockAuthService.shouldSucceed = false

        let expectation = self.expectation(description: "Login fails")

        // Act
        viewModel.login(email: "test@example.com", password: "wrong") { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure")
            case .failure(let error):
                XCTAssertEqual(error, .invalidCredentials)
                expectation.fulfill()
            }
        }

        waitForExpectations(timeout: 1.0)
    }

    func testEmailValidation() {
        XCTAssertFalse(viewModel.isValidEmail("invalid"))
        XCTAssertFalse(viewModel.isValidEmail("test@"))
        XCTAssertTrue(viewModel.isValidEmail("test@example.com"))
    }
}

// Mock
class MockAuthService: AuthServiceProtocol {
    var shouldSucceed = true

    func login(email: String, password: String, completion: @escaping (Result<User, AuthError>) -> Void) {
        if shouldSucceed {
            completion(.success(User(id: "1", email: email)))
        } else {
            completion(.failure(.invalidCredentials))
        }
    }
}
```

### Android Unit Testing (JUnit + Mockito)

**Testing a ViewModel:**
```kotlin
import org.junit.Before
import org.junit.Test
import org.junit.Assert.*
import org.mockito.Mock
import Mockito.*
import org.mockito.MockitoAnnotations
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest

@ExperimentalCoroutinesApi
class LoginViewModelTest {
    @Mock
    private lateinit var authRepository: AuthRepository

    private lateinit var viewModel: LoginViewModel

    @Before
    fun setup() {
        MockitoAnnotations.openMocks(this)
        viewModel = LoginViewModel(authRepository)
    }

    @Test
    fun `login success updates state`() = runTest {
        // Arrange
        val email = "test@example.com"
        val password = "password123"
        val user = User(id = "1", email = email)

        `when`(authRepository.login(email, password)).thenReturn(Result.success(user))

        // Act
        viewModel.login(email, password)

        // Assert
        assertTrue(viewModel.uiState.value.isLoggedIn)
        assertNull(viewModel.uiState.value.error)
    }

    @Test
    fun `login failure shows error`() = runTest {
        // Arrange
        val email = "test@example.com"
        val password = "wrong"
        val error = AuthError.InvalidCredentials

        `when`(authRepository.login(email, password)).thenReturn(Result.failure(error))

        // Act
        viewModel.login(email, password)

        // Assert
        assertFalse(viewModel.uiState.value.isLoggedIn)
        assertEquals(error, viewModel.uiState.value.error)
    }

    @Test
    fun `email validation works correctly`() {
        assertFalse(viewModel.isValidEmail("invalid"))
        assertFalse(viewModel.isValidEmail("test@"))
        assertTrue(viewModel.isValidEmail("test@example.com"))
    }
}
```

### Best Practices

1. **Use dependency injection** - Makes testing easier
2. **Mock external dependencies** - Network, database, sensors
3. **Test one thing per test** - Clear, focused tests
4. **Use descriptive test names** - What is being tested
5. **Arrange-Act-Assert pattern** - Clear test structure
6. **Test edge cases** - Empty, null, boundary values
7. **Keep tests fast** - Unit tests should be < 100ms

## Integration Testing

### What to Test

**API Integration:**
- Network requests and responses
- Error handling
- Data parsing
- Authentication flow

**Database Integration:**
- CRUD operations
- Queries
- Migrations
- Relationships

**Component Integration:**
- Screen navigation
- Data flow between components
- State management

### iOS Integration Testing

**Testing API Integration:**
```swift
import XCTest
@testable import MyApp

class APIClientTests: XCTestCase {
    var apiClient: APIClient!
    var mockURLSession: MockURLSession!

    override func setUp() {
        super.setUp()
        mockURLSession = MockURLSession()
        apiClient = APIClient(session: mockURLSession)
    }

    func testFetchUsers() {
        // Arrange
        let expectedUsers = [User(id: "1", name: "John")]
        let data = try! JSONEncoder().encode(expectedUsers)
        mockURLSession.data = data
        mockURLSession.response = HTTPURLResponse(url: URL(string: "https://api.example.com")!,
                                                   statusCode: 200,
                                                   httpVersion: nil,
                                                   headerFields: nil)

        let expectation = self.expectation(description: "Fetch users")

        // Act
        apiClient.fetchUsers { result in
            // Assert
            switch result {
            case .success(let users):
                XCTAssertEqual(users.count, 1)
                XCTAssertEqual(users[0].name, "John")
                expectation.fulfill()
            case .failure:
                XCTFail("Expected success")
            }
        }

        waitForExpectations(timeout: 1.0)
    }

    func testFetchUsersNetworkError() {
        // Arrange
        mockURLSession.error = NSError(domain: "Network", code: -1009, userInfo: nil)

        let expectation = self.expectation(description: "Network error")

        // Act
        apiClient.fetchUsers { result in
            // Assert
            switch result {
            case .success:
                XCTFail("Expected failure")
            case .failure(let error):
                XCTAssertEqual(error, .networkError)
                expectation.fulfill()
            }
        }

        waitForExpectations(timeout: 1.0)
    }
}
```

**Testing Database (Core Data):**
```swift
class DatabaseTests: XCTestCase {
    var context: NSManagedObjectContext!

    override func setUp() {
        super.setUp()
        // Use in-memory store for testing
        let container = NSPersistentContainer(name: "Model")
        let description = NSPersistentStoreDescription()
        description.type = NSInMemoryStoreType
        container.persistentStoreDescriptions = [description]

        container.loadPersistentStores { _, error in
            XCTAssertNil(error)
        }

        context = container.viewContext
    }

    func testSaveUser() {
        // Arrange
        let user = User(context: context)
        user.id = "1"
        user.name = "John"

        // Act
        try? context.save()

        // Assert
        let fetchRequest: NSFetchRequest<User> = User.fetchRequest()
        let users = try? context.fetch(fetchRequest)

        XCTAssertEqual(users?.count, 1)
        XCTAssertEqual(users?.first?.name, "John")
    }
}
```

### Android Integration Testing

**Testing Repository:**
```kotlin
@RunWith(AndroidJUnit4::class)
class UserRepositoryTest {
    private lateinit var database: AppDatabase
    private lateinit var userDao: UserDao
    private lateinit var repository: UserRepository

    @Before
    fun setup() {
        // Use in-memory database
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).build()

        userDao = database.userDao()
        repository = UserRepository(userDao)
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun insertAndGetUser() = runBlocking {
        // Arrange
        val user = User(id = "1", name = "John")

        // Act
        repository.insertUser(user)
        val retrieved = repository.getUser("1")

        // Assert
        assertEquals(user.name, retrieved?.name)
    }

    @Test
    fun getAllUsers() = runBlocking {
        // Arrange
        val users = listOf(
            User(id = "1", name = "John"),
            User(id = "2", name = "Jane")
        )

        // Act
        users.forEach { repository.insertUser(it) }
        val allUsers = repository.getAllUsers()

        // Assert
        assertEquals(2, allUsers.size)
    }
}
```

## UI/E2E Testing

### iOS UI Testing (XCUITest)

**Testing Login Flow:**
```swift
import XCTest

class LoginUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    func testSuccessfulLogin() {
        // Arrange
        let emailField = app.textFields["emailTextField"]
        let passwordField = app.secureTextFields["passwordTextField"]
        let loginButton = app.buttons["loginButton"]

        // Act
        emailField.tap()
        emailField.typeText("test@example.com")

        passwordField.tap()
        passwordField.typeText("password123")

        loginButton.tap()

        // Assert
        let dashboardTitle = app.staticTexts["Dashboard"]
        XCTAssertTrue(dashboardTitle.waitForExistence(timeout: 5))
    }

    func testLoginWithInvalidCredentials() {
        // Arrange
        let emailField = app.textFields["emailTextField"]
        let passwordField = app.secureTextFields["passwordTextField"]
        let loginButton = app.buttons["loginButton"]

        // Act
        emailField.tap()
        emailField.typeText("wrong@example.com")

        passwordField.tap()
        passwordField.typeText("wrongpassword")

        loginButton.tap()

        // Assert
        let errorAlert = app.alerts["Error"]
        XCTAssertTrue(errorAlert.waitForExistence(timeout: 2))
    }

    func testEmptyFieldsShowValidation() {
        // Act
        let loginButton = app.buttons["loginButton"]
        loginButton.tap()

        // Assert
        let emailError = app.staticTexts["Email is required"]
        XCTAssertTrue(emailError.exists)
    }
}
```

### Android UI Testing (Espresso)

**Testing Login Flow:**
```kotlin
@RunWith(AndroidJUnit4::class)
class LoginActivityTest {
    @get:Rule
    val activityRule = ActivityScenarioRule(LoginActivity::class.java)

    @Test
    fun successfulLogin() {
        // Arrange & Act
        onView(withId(R.id.emailEditText))
            .perform(typeText("test@example.com"), closeSoftKeyboard())

        onView(withId(R.id.passwordEditText))
            .perform(typeText("password123"), closeSoftKeyboard())

        onView(withId(R.id.loginButton))
            .perform(click())

        // Assert
        onView(withId(R.id.dashboardTitle))
            .check(matches(isDisplayed()))
    }

    @Test
    fun loginWithInvalidCredentials() {
        // Arrange & Act
        onView(withId(R.id.emailEditText))
            .perform(typeText("wrong@example.com"), closeSoftKeyboard())

        onView(withId(R.id.passwordEditText))
            .perform(typeText("wrongpassword"), closeSoftKeyboard())

        onView(withId(R.id.loginButton))
            .perform(click())

        // Assert
        onView(withText("Invalid credentials"))
            .check(matches(isDisplayed()))
    }

    @Test
    fun emptyFieldsShowValidation() {
        // Act
        onView(withId(R.id.loginButton))
            .perform(click())

        // Assert
        onView(withText("Email is required"))
            .check(matches(isDisplayed()))
    }
}
```

### Jetpack Compose UI Testing

```kotlin
@RunWith(AndroidJUnit4::class)
class LoginScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun successfulLogin() {
        // Arrange
        composeTestRule.setContent {
            LoginScreen()
        }

        // Act
        composeTestRule.onNodeWithTag("emailField")
            .performTextInput("test@example.com")

        composeTestRule.onNodeWithTag("passwordField")
            .performTextInput("password123")

        composeTestRule.onNodeWithTag("loginButton")
            .performClick()

        // Assert
        composeTestRule.onNodeWithText("Dashboard")
            .assertIsDisplayed()
    }
}
```

## Device Testing Requirements

### Test on Real Devices

**Minimum Device Matrix:**

**iOS:**
- Latest iPhone (current iOS)
- iPhone from 2 years ago (iOS N-1)
- iPad (latest iOS)
- Test on physical devices, not just simulator

**Android:**
- Flagship device (latest Android)
- Mid-range device (Android N-1)
- Low-end device (Android N-2)
- Different manufacturers (Samsung, Google, Xiaomi)
- Different screen sizes (small, medium, large)

### Why Real Devices Matter

**Simulators/Emulators miss:**
- Real performance characteristics
- Memory constraints
- Battery impact
- Camera/sensors behavior
- Network conditions
- Touch/gesture accuracy
- Device-specific bugs

### Testing Scenarios

1. **Network Conditions:**
   - WiFi, 4G, 3G, offline
   - Switching between networks
   - Airplane mode

2. **Interruptions:**
   - Incoming call
   - SMS/notification
   - Low battery warning
   - App switching

3. **Lifecycle:**
   - App backgrounding
   - Process death (kill app)
   - Low memory
   - Configuration changes (rotation)

4. **Permissions:**
   - Granting permissions
   - Denying permissions
   - Revoking permissions in settings

## Test Automation in CI/CD

### iOS (Fastlane + XCTest)

```ruby
# Fastfile
lane :test do
  run_tests(
    scheme: "MyApp",
    devices: ["iPhone 14", "iPad Pro (12.9-inch)"],
    clean: true
  )
end

lane :ui_test do
  run_tests(
    scheme: "MyAppUITests",
    devices: ["iPhone 14"],
    clean: true
  )
end
```

### Android (Gradle)

```gradle
// build.gradle
android {
    testOptions {
        unitTests {
            includeAndroidResources = true
        }
    }
}

// Run tests
./gradlew test           // Unit tests
./gradlew connectedTest  // Instrumented tests
```

### GitHub Actions Example

```yaml
name: Mobile Tests

on: [push, pull_request]

jobs:
  ios-tests:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          xcodebuild test \
            -scheme MyApp \
            -destination 'platform=iOS Simulator,name=iPhone 14'

  android-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up JDK
        uses: actions/setup-java@v3
        with:
          java-version: '17'
      - name: Run unit tests
        run: ./gradlew test
      - name: Run instrumented tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          script: ./gradlew connectedCheck
```

## Performance Testing

### iOS (Instruments)

- Time Profiler (CPU usage)
- Allocations (memory usage)
- Leaks (memory leaks)
- Network (network activity)
- Energy Log (battery impact)

### Android (Profiler)

- CPU Profiler
- Memory Profiler
- Network Profiler
- Energy Profiler

### Metrics to Track

- App startup time (< 2s cold start)
- Screen load time (< 1s)
- Frame rate (60fps, no jank)
- Memory usage (< 100MB for simple apps)
- Battery drain (< 5% per hour active use)
- APK/IPA size (< 50MB)

## Testing Checklist

Before release:

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] UI tests for critical flows passing
- [ ] Tested on real devices (iOS and Android)
- [ ] Tested on different OS versions
- [ ] Tested on different screen sizes
- [ ] Tested offline functionality
- [ ] Tested with poor network
- [ ] Tested app backgrounding/foregrounding
- [ ] Tested process death scenario
- [ ] Tested permission flows
- [ ] Tested interruptions (calls, notifications)
- [ ] Performance profiled (no memory leaks)
- [ ] Battery impact measured
- [ ] Crash-free rate > 99%

## Common Testing Mistakes

1. **Only testing on simulator/emulator** - Real devices behave differently
2. **Not testing offline** - Network is unreliable
3. **Not testing process death** - App can be killed anytime
4. **Not testing on low-end devices** - Performance issues
5. **Not testing permissions** - Users can deny
6. **Not testing interruptions** - Calls, notifications happen
7. **Skipping UI tests** - Critical flows need E2E coverage
8. **Not measuring performance** - Memory leaks, battery drain
9. **Not testing on different OS versions** - API differences
10. **Not automating tests** - Manual testing doesn't scale

## Resources

- [iOS Testing Guide](https://developer.apple.com/documentation/xctest)
- [Android Testing Guide](https://developer.android.com/training/testing)
- [Espresso Documentation](https://developer.android.com/training/testing/espresso)
- [XCUITest Documentation](https://developer.apple.com/documentation/xctest/user_interface_tests)
- [Fastlane Documentation](https://docs.fastlane.tools/)
