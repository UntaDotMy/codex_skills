# Web State Management Patterns

## When to Use What

### Decision Matrix

| Scenario | Recommended Solution | Why |
|----------|---------------------|-----|
| Component-local state | `useState` | Simple, no sharing needed |
| Form state | `useState` + validation library | Controlled inputs, validation |
| Shared state (2-3 components) | Props or Context | Simple prop drilling or Context |
| App-wide state (theme, auth) | Context API | Built-in, no dependencies |
| Complex app state | Redux Toolkit | Predictable, debuggable, middleware |
| Server state (API data) | React Query / SWR | Caching, revalidation, optimistic updates |
| URL state (filters, pagination) | URL params + `useSearchParams` | Shareable, bookmarkable |
| Global state (simple) | Zustand | Minimal boilerplate, easy to use |
| Performance-critical | Jotai / Recoil | Atomic updates, fine-grained reactivity |

## Local State (useState)

**Use for:**
- Component-specific state
- Form inputs
- UI state (open/closed, selected)
- Temporary data

**Example:**
```javascript
function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

**When NOT to use:**
- State needed by multiple components
- State that needs to persist
- Complex state with many updates

## Context API

**Use for:**
- Theme (dark/light mode)
- Authentication state
- User preferences
- Localization (i18n)
- Shared UI state (sidebar open/closed)

**Example:**
```javascript
const ThemeContext = createContext();

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

**Pros:**
- Built into React
- No dependencies
- Simple for small-medium apps

**Cons:**
- Can cause unnecessary re-renders
- No built-in devtools
- Can become complex with many contexts

**Best practices:**
- Split contexts by concern (don't put everything in one)
- Use `useMemo` for context values to prevent re-renders
- Consider using `useReducer` for complex state logic

## Redux Toolkit

**Use for:**
- Large applications with complex state
- State that needs to be shared across many components
- State that needs middleware (logging, persistence)
- When you need time-travel debugging

**Example:**
```javascript
// store/counterSlice.js
import { createSlice } from '@reduxjs/toolkit';

const counterSlice = createSlice({
  name: 'counter',
  initialState: { value: 0 },
  reducers: {
    increment: (state) => {
      state.value += 1; // Immer allows "mutation"
    },
    decrement: (state) => {
      state.value -= 1;
    },
  },
});

export const { increment, decrement } = counterSlice.actions;
export default counterSlice.reducer;

// Component
function Counter() {
  const count = useSelector((state) => state.counter.value);
  const dispatch = useDispatch();

  return (
    <button onClick={() => dispatch(increment())}>
      Count: {count}
    </button>
  );
}
```

**Pros:**
- Predictable state updates
- Excellent devtools (Redux DevTools)
- Middleware support
- Large ecosystem

**Cons:**
- More boilerplate than alternatives
- Learning curve
- Can be overkill for simple apps

**Best practices:**
- Use Redux Toolkit (not vanilla Redux)
- Normalize state shape (avoid nested data)
- Use selectors with `reselect` for derived data
- Keep reducers pure (no side effects)
- Use `createAsyncThunk` for async logic

## React Query / TanStack Query

**Use for:**
- Fetching data from APIs
- Caching server state
- Background refetching
- Optimistic updates
- Pagination and infinite scroll

**Example:**
```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function TodoList() {
  const queryClient = useQueryClient();

  // Fetch todos
  const { data, isLoading, error } = useQuery({
    queryKey: ['todos'],
    queryFn: () => fetch('/api/todos').then(res => res.json()),
    staleTime: 5000, // Consider fresh for 5s
  });

  // Add todo
  const mutation = useMutation({
    mutationFn: (newTodo) => fetch('/api/todos', {
      method: 'POST',
      body: JSON.stringify(newTodo),
n    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data.map(todo => <div key={todo.id}>{todo.title}</div>)}
      <button onClick={() => mutation.mutate({ title: 'New Todo' })}>
        Add Todo
      </button>
    </div>
  );
}
```

**Pros:**
- Automatic caching and revalidation
- Loading and error states built-in
- Optimistic updates
- Pagination and infinite scroll support
- Devtools

**Cons:**
- Another dependency
- Learning curve
- Not for client-only state

**Best practices:**
- Use query keys consistently
- Set appropriate `staleTime` and `cacheTime`
- Use optimistic updates for better UX
- Handle loading and error states
- Use `useQueryClient` for manual cache updates

## SWR (Similar to React Query)

**Use for:** Same as React Query

**Example:**
```javascript
import useSWR from 'swr';

const fetcher = (url) => fetch(url).then(res => res.json());

function Profile() {
  const { data, error, isLoading } = useSWR('/api/user', fetcher);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error</div>;

  return <div>Hello {data.name}!</div>;
}
```

**Pros:**
- Lightweight
- Simple API
- Automatic revalidation
- Built-in cache

**Cons:**
- Less features than React Query
- Smaller ecosystem

## Zustand

**Use for:**
- Simple global state
- When Redux feels too heavy
- When Context causes too many re-renders

**Example:**
```javascript
import { create } from 'zustand';

const useStore = create((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}));

function Counter() {
  const { count, increment } = useStore();

  return (
    <button onClick={increment}>
      Count: {count}
    </button>
  );
}
```

**Pros:**
- Minimal boilerplate
- No providers needed
- Small bundle size (~1KB)
- Easy to learn

**Cons:**
- No built-in devtools (can add middleware)
- Less structure than Redux
- Smaller ecosystem

**Best practices:**
- Split stores by domain
- Use selectors to prevent re-renders
- Use middleware for persistence, devtools

## Jotai (Atomic State)

**Use for:**
- Fine-grained reactivity
- Performance-critical apps
- When you want atomic updates

**Example:**
```javascript
import { atom, useAtom } from 'jotai';

const countAtom = atom(0);

function Counter() {
  const [count, setCount] = useAtom(countAtom);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

**Pros:**
- Atomic updates (only affected components re-render)
- TypeScript-first
- Small bundle size
- Composable atoms

**Cons:**
- Different mental model
- Smaller ecosystem
- Learning curve

## URL State

**Use for:**
- Filters
- Pagination
- Search queries
- Tabs
- Any state that should be shareable/bookmarkable

**Example:**
```javascript
import { useSearchParams } from 'react-router-dom';

function ProductList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = searchParams.get('page') || '1';
  const filter = searchParams.get('filter') || 'all';

  const updateFilter = (newFilter) => {
    setSearchParams({ page: '1', filter: newFilter });
  };

  return (
    <div>
      <button onClick={() => updateFilter('active')}>Active</button>
      <button onClick={() => updateFilter('completed')}>Completed</button>
      {/* Products for current page and filter */}
    </div>
  );
}
```

**Pros:**
- Shareable URLs
- Bookmarkable state
- Browser back/forward works
- SEO-friendly

**Cons:**
- Limited to serializable data
- URL length limits
- Not for sensitive data

## Common Anti-Patterns

### 1. Prop Drilling Hell
**Problem:** Passing props through many levels

**Solution:** Use Context or state management library

### 2. Everything in Redux
**Problem:** Putting all state in Redux, including local UI state

**Solution:** Use local state for component-specific state

### 3. Context for Everything
**Problem:** One giant context with all app state

**Solution:** Split contexts by concern, use state management library for complex state

### 4. Not Using Server State Libraries
**Problem:** Managing API data with useState/useEffect

**Solution:** Use React Query or SWR for server state

### 5. Derived State in State
**Problem:** Storing computed values in state

**Solution:** Calculate derived values during render or use memoization

**Bad:**
```javascript
const [items, setItems] = useState([]);
const [itemCount, setItemCount] = useState(0); // Derived!

// Have to keep in sync
setItems(newItems);
setItemCount(newItems.length);
```

**Good:**
```javascript
const [items, setItems] = useState([]);
const itemCount = items.length; // Calculated
```

### 6. Unnecessary Re-renders
**Problem:** Context value changes cause all consumers to re-render

**Solution:** Split contexts, use selectors, memoize values

**Bad:**
```javascript
<Context.Provider value={{ user, theme, settings }}>
```

**Good:**
```javascript
<UserContext.Provider value={user}>
  <ThemeContext.Provider value={theme}>
    <SettingsContext.Provider value={settings}>
```

## Migration Strategies

### From Context to Redux
1. Identify state that needs Redux (complex, shared)
2. Create Redux slices for that state
3. Gradually move state from Context to Redux
4. Keep Context for simple state (theme, auth)

### From Redux to React Query
1. Identify server state in Redux
2. Replace with React Query queries/mutations
3. Keep Redux for client state only
4. Remove unnecessary Redux code

### From useState to Zustand
1. Identify state shared across components
2. Create Zustand store
3. Replace useState with useStore
4. Remove prop drilling

## Choosing the Right Solution

**Start simple:**
1. Use `useState` for local state
2. Use props for sharing between parent/child
3. Use Context for app-wide state (theme, auth)
4. Use React Query for server state

**Scale up when needed:**
- Context causing performance issues? → Zustand or Redux
- Complex state logic? → Redux Toolkit
- Need time-travel debugging? → Redux DevTools
- Need atomic updates? → Jotai or Recoil

**Don't over-engineer:**
- Small app? Context is fine
- No server state? Don't add React Query
- Simple state? Don't add Redux

## Resources

- [Redux Toolkit](https://redux-toolkit.js.org/)
- [React Query](https://tanstack.com/query/latest)
- [SWR](https://swr.vercel.app/)
- [Zustand](https://github.com/pmndrs/zustand)
- [Jotai](https://jotai.org/)
- [Recoil](https://recoiljs.org/)
