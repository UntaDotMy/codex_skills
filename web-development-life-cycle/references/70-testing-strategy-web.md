# Web Testing Strategy

## Testing Pyramid

```
        /\
       /E2E\
      /------\
     /Integration\
    /--------------\
   /   Unit Tests   \
  /------------------\
```

**Ratio:** 70% Unit, 20% Integration, 10% E2E

## Unit Testing

### What to Test

**Business Logic:**
- Pure functions
- Data transformations
- Calculations and algorithms
- Validation logic
- Utility functions

**React Components:**
- Rendering with different props
- User interactions (clicks, inputs)
- Conditional rendering
- State changes
- Event handlers

**Hooks:**
- Custom hooks behavior
- State updates
- Side effects

### What NOT to Test

- Third-party libraries (trust they're tested)
- Implementation details (internal state, private methods)
- Trivial code (getters, setters)
- Framework code (React itself)

### Tools

**Test Runners:**
- Jest (most popular, batteries included)
- Vitest (faster, Vite-compatible)

**React Testing:**
- React Testing Library (recommended)
- Enzyme (legacy, not recommended)

**Assertions:**
- Jest matchers
- Testing Library queries

### Examples

**Testing a Pure Function:**
```javascript
// utils/math.js
export function add(a, b) {
  return a + b;
}

// utils/math.test.js
import { add } from './math';

describe('add', () => {
  it('adds two positive numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  it('adds negative numbers', () => {
    expect(add(-2, -3)).toBe(-5);
  });

  it('handles zero', () => {
    expect(add(0, 5)).toBe(5);
  });
});
```

**Testing a React Component:**
```javascript
// Button.jsx
export function Button({ onClick, children, disabled }) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

// Button.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick} disabled>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).not.toHaveBeenCalled();
  });
});
```

**Testing a Custom Hook:**
```javascript
// useCounter.js
import { useState } from 'react';

export function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);

  const increment = () => setCount(c => c + 1);
  const decrement = () => setCount(c => c - 1);
  const reset = () => setCount(initialValue);

  return { count, increment, decrement, reset };
}

// useCounter.test.js
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it('initializes with custom value', () => {
    const { result } = renderHook(() => useCounter(10));
    expect(result.current.count).toBe(10);
  });

  it('increments count', () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it('resets to initial value', () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.increment();
      result.current.increment();
      result.current.reset();
    });

    expect(result.current.count).toBe(5);
  });
});
```

### Best Practices

1. **Test behavior, not implementation**
2. **Use descriptive test names** (what it does, not how)
3. **Arrange-Act-Assert pattern**
4. **One assertion per test** (when possible)
5. **Test edge cases** (empty, null, undefined, boundary values)
6. **Mock external dependencies** (APIs, timers, random)
7. **Keep tests fast** (< 1s per test)

## Integration Testing

### What to Test

**Component Integration:**
- Parent-child component interaction
- Context providers and consumers
- Form submission flows
- Multi-step processes

**API Integration:**
- API calls with mocked responses
- Error handling
- Loading states
- Data transformation

**State Management:**
- Redux actions and reducers
- Context updates
- State persistence

### Tools

- React Testing Library (component integration)
- MSW (Mock Service Worker) for API mocking
- Redux mock store

### Examples

**Testing Component Integration:**
```javascript
// TodoApp.jsx
function TodoApp() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState('');

  const addTodo = () => {
    if (input.trim()) {
      setTodos([...todos, { id: Date.now(), text: input }]);
      setInput('');
    }
  };

  return (
    <div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Add todo"
      />
      <button onClick={addTodo}>Add</button>
      <ul>
        {todos.map(todo => (
          <li key={todo.id}>{todo.text}</li>
        ))}
      </ul>
    </div>
  );
}

// TodoApp.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TodoApp } from './TodoApp';

describe('TodoApp', () => {
  it('adds a todo when button is clicked', () => {
    render(<TodoApp />);

    const input = screen.getByPlaceholderText('Add todo');
    const button = screen.getByText('Add');

    fireEvent.change(input, { target: { value: 'Buy milk' } });
    fireEvent.click(button);

    expect(screen.getByText('Buy milk')).toBeInTheDocument();
    expect(input.value).toBe(''); // Input cleared
  });

  it('does not add empty todos', () => {
    render(<TodoApp />);

    const button = screen.getByText('Add');
    fireEvent.click(button);

    expect(screen.queryByRole('listitem')).not.toBeInTheDocument();
  });
});
```

**Testing API Integration with MSW:**
```javascript
// api.js
export async function fetchUsers() {
  const response = await fetch('/api/users');
  if (!response.ok) throw new Error('Failed to fetch');
  return response.json();
}

// UserList.jsx
function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

// UserList.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { UserList } from './UserList';

const server = setupServer(
  rest.get('/api/users', (req, res, ctx) => {
    return res(ctx.json([
      { id: 1, name: 'John' },
      { id: 2, name: 'Jane' },
    ]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UserList', () => {
  it('displays users after loading', async () => {
    render(<UserList />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('John')).toBeInTheDocument();
      expect(screen.getByText('Jane')).toBeInTheDocument();
    });
  });

  it('displays error on fetch failure', async () => {
    server.use(
      rest.get('/api/users', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText(/Error/)).toBeInTheDocument();
    });
  });
});
```

### Best Practices

1. **Mock external dependencies** (APIs, databases)
2. **Test happy path and error cases**
3. **Test loading states**
4. **Use realistic test data**
5. **Clean up after tests** (reset mocks, clear state)

## End-to-End (E2E) Testing

### What to Test

**Critical User Flows:**
- User registration and login
- Checkout process
- Form submissions
- Navigation flows
- Search functionality

**Cross-Browser:**
- Chrome, Firefox, Safari
- Mobile browsers

### Tools

**Playwright (Recommended):**
- Fast, reliable
- Multi-browser support
- Auto-wait for elements
- Network interception
- Screenshots and videos

**Cypress:**
- Developer-friendly
- Time-travel debugging
- Real-time reloading

**Selenium:**
- Legacy, not recommended for new projects

### Examples

**Playwright Test:**
```javascript
// tests/login.spec.js
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('successful login', async ({ page }) => {
    await page.goto('http://localhost:3000/login');

    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('http://localhost:3000/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/login');

    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });

  test('validates required fields', async ({ page }) => {
    await page.goto('http://localhost:3000/login');

    await page.click('button[type="submit"]');

    await expect(page.locator('input[name="email"]:invalid')).toBeVisible();
  });
});
```

**Testing with Network Interception:**
```javascript
test('handles slow API responses', async ({ page }) => {
  await page.route('**/api/users', async route => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    await route.fulfill({
      status: 200,
      body: JSON.stringify([{ id: 1, name: 'John' }]),
    });
  });

  await page.goto('http://localhost:3000/users');

  await expect(page.locator('.loading')).toBeVisible();
  await expect(page.locator('text=John')).toBeVisible({ timeout: 5000 });
});
```

### Best Practices

1. **Test critical paths only** (E2E is slow and expensive)
2. **Use data-testid attributes** for stable selectors
3. **Run in CI/CD pipeline**
4. **Parallelize tests** for speed
5. **Take screenshots on failure**
6. **Test on real browsers**, not just headless
7. **Keep tests independent** (no shared state)
8. **Use page objects** for maintainability

## Coverage Targets

### Recommended Coverage

- **Unit Tests**: 70-80% coverage
- **Integration Tests**: Critical flows covered
- **E2E Tests**: Happy paths for critical features

### What Coverage Doesn't Tell You

- Code coverage ≠ good tests
- 100% coverage doesn't mean bug-free
- Focus on testing behavior, not coverage numbers

### Measuring Coverage

```bash
# Jest
npm test -- --coverage

# Vitest
npm test -- --coverage

# View HTML report
open coverage/index.html
```

## Test Organization

### File Structure

```
src/
  components/
    Button/
      Button.jsx
      Button.test.jsx
      Button.module.css
  utils/
    math.js
    math.test.js
tests/
  e2e/
    login.spec.js
    checkout.spec.js
```

### Naming Conventions

- Unit/Integration: `*.test.js` or `*.spec.js`
- E2E: `*.spec.js` in `tests/e2e/`

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm test -- --coverage

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Common Testing Mistakes

1. **Testing implementation details** - Test behavior, not internal state
2. **Not testing edge cases** - Test empty, null, boundary values
3. **Flaky tests** - Tests that randomly fail (fix or remove)
4. **Slow tests** - Keep unit tests fast (< 1s)
5. **Too many E2E tests** - E2E is slow, focus on critical paths
6. **Not mocking external dependencies** - Tests should be isolated
7. **Skipping tests** - Fix or remove, don't skip
8. **Not running tests in CI** - Tests must run on every commit

## Testing Checklist

Before marking feature complete:

- [ ] Unit tests for business logic
- [ ] Integration tests for component interactions
- [ ] E2E test for critical user flow (if applicable)
- [ ] All tests passing
- [ ] No skipped tests (`.skip()`)
- [ ] Coverage maintained or improved
- [ ] Tests run in CI/CD
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Loading states tested

## Resources

- [React Testing Library](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [MSW (Mock Service Worker)](https://mswjs.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
