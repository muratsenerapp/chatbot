# Frontend - Chatbot UI

A modern, responsive React application built with TypeScript and Vite that provides a real-time chat interface with streaming responses. Features a clean, minimal design with dark/light theme support and comprehensive error handling.

## Technology Stack

- **React 19.1.1** - Modern UI library with latest features
- **TypeScript 5.9.3** - Type-safe development
- **Vite 7.1.7** - Fast build tool and development server
- **Tailwind CSS 3.4.18** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library
- **Vitest** - Fast unit testing framework
- **Testing Library** - React component testing utilities

## Prerequisites

- Node.js 22.x (specified in `.nvmrc` and `package.json`)
- npm 10.9.3+ (specified in `packageManager`)
- Backend API running on http://localhost:8000

## Local Development Setup

### 1. Install Node.js

Using nvm (recommended):

```bash
# Install nvm if not already installed
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use the correct Node version
nvm install
nvm use
```

Or download Node.js 22.x directly from [nodejs.org](https://nodejs.org/).

### 2. Install Dependencies

```bash
cd frontend
npm install
```

### 3. Run the Frontend

Start the development server with hot module replacement:

```bash
npm run dev
```

The application will be available at http://localhost:5173

The Vite dev server is configured to proxy API requests from `/api/*` to the backend at `http://localhost:8000`.

## Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Type checking
npm run typecheck

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Generate test coverage report
npm run coverage
```

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── chat/
│   │   │   ├── Chat.tsx     # Main chat container with state management
│   │   │   ├── MessageBubble.tsx  # Message display component
│   │   │   ├── InputBar.tsx       # User input component
│   │   │   └── streamUtils.ts    # Stream management utilities
│   │   └── ThemeToggle.tsx       # Dark/light theme toggle
│   │
│   ├── lib/
│   │   └── sseClient.ts           # Server-Sent Events client library
│   │
│   ├── types/
│   │   └── chat.ts          # TypeScript type definitions
│   │
│   ├── App.tsx              # Root application component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles and Tailwind directives
│
├── tests/                   # Test files
│   ├── sseClient.test.ts     # SSE client tests
│   ├── streamUtils.test.ts # Stream utility tests
│   └── setup.ts            # Test configuration
│
├── public/                  # Static assets
│
├── vite.config.ts          # Vite configuration
├── vitest.config.ts        # Vitest configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript base configuration
├── tsconfig.app.json       # App TypeScript configuration
├── tsconfig.node.json      # Node TypeScript configuration
├── tsconfig.test.json      # Test TypeScript configuration
├── eslint.config.js        # ESLint configuration
├── postcss.config.js       # PostCSS configuration
├── package.json            # Dependencies and scripts
└── .nvmrc                  # Node version specification
```

## Key Features

### Real-Time Streaming

The application uses Server-Sent Events (SSE) to receive token-by-token responses from the backend, providing a smooth, real-time chat experience.

**Implementation:** `src/lib/sseClient.ts` and `src/components/chat/Chat.tsx`

### Session Management

Conversations are maintained across multiple messages using session IDs. The backend tracks conversation history per session, allowing for contextual responses.

### Theme Support

Automatic dark/light theme switching with system preference detection:
- Detects system color scheme preference
- Persists user theme choice in localStorage
- Smooth transitions between themes

**Implementation:** `src/components/ThemeToggle.tsx`

### Error Handling

Comprehensive error handling with user-friendly feedback:
- Network error detection
- Server error messages
- Retry functionality for failed requests
- Graceful degradation

### Responsive Design

Mobile-first responsive design using Tailwind CSS:
- Adapts to different screen sizes
- Touch-friendly interface
- Optimized for both desktop and mobile

## Configuration

### API Proxy

The Vite development server is configured to proxy API requests to the backend. This configuration is in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

To change the backend URL, modify the `target` value.

### Path Aliases

TypeScript path aliases are configured for cleaner imports:

```typescript
// Instead of: import Chat from '../../components/chat/Chat'
import Chat from '@/components/chat/Chat'
```

Configuration in `vite.config.ts` and `tsconfig.app.json`.

### Tailwind Configuration

Tailwind CSS is configured with custom theme settings in `tailwind.config.js`. The default configuration includes:
- Dark mode via `class` strategy
- Custom color schemes
- Extended spacing and sizing utilities

## Development

### Code Style

The project uses ESLint for code quality and consistency:

```bash
# Check for linting errors
npm run lint

# Many errors can be auto-fixed (be careful!)
# npm run lint -- --fix
```

ESLint is configured with:
- React-specific rules
- React Hooks rules
- TypeScript-ESLint rules
- React Fast Refresh support

### Type Checking

TypeScript provides type safety across the application:

```bash
# Run type checking
npm run typecheck
```

Type checking is separated from the build process for faster feedback during development.

### Component Development

When creating new components:

1. Place components in `src/components/` with logical subdirectories
2. Use TypeScript for all component files (`.tsx`)
3. Define prop types using TypeScript interfaces
4. Export components as default exports
5. Co-locate component-specific utilities in the same directory

**Example:**

```typescript
interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

export default function MyComponent({ title, onAction }: MyComponentProps) {
  return (
    <div>
      <h2>{title}</h2>
      <button onClick={onAction}>Action</button>
    </div>
  );
}
```

## Testing

### Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run coverage
```

### Test Structure

Tests are located in the `tests/` directory and use:
- **Vitest** - Fast test runner
- **Testing Library** - React component testing
- **jsdom** - Browser environment simulation

### Writing Tests

Tests should:
- Focus on user behavior rather than implementation details
- Use Testing Library's query methods (`getByRole`, `getByText`, etc.)
- Test component integration, not isolated units
- Mock external dependencies (API calls, etc.)

**Example:**

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import MyComponent from '@/components/MyComponent';

describe('MyComponent', () => {
  it('renders title correctly', () => {
    render(<MyComponent title="Hello" />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Running with Docker

This project is designed for **local/self-hosted use via Docker**. The recommended way to run is using the root `docker-compose.yml`:

```bash
# From project root
docker compose up -d
```

The frontend will be available at http://localhost:5173 and automatically proxies API requests to the backend.

See the [root README](../README.md) for complete Docker setup instructions.

## Troubleshooting

### Backend Connection Issues

**Problem:** API requests fail with network errors

**Solutions:**
1. Verify backend is running on http://localhost:8000
2. Check backend health endpoint: http://localhost:8000/api/health
3. Review Vite proxy configuration in `vite.config.ts`
4. Check browser console for CORS errors

### Build Errors

**Problem:** TypeScript errors during build

**Solutions:**
1. Run type checking separately: `npm run typecheck`
2. Fix type errors before building
3. Ensure all dependencies are installed: `npm install`

### Theme Not Persisting

**Problem:** Theme resets on page reload

**Solutions:**
1. Check browser localStorage is enabled
2. Verify no errors in browser console
3. Clear localStorage and retry: `localStorage.clear()`

### Tests Failing

**Problem:** Tests fail unexpectedly

**Solutions:**
1. Ensure all dependencies are installed: `npm install`
2. Clear test cache: `npm run test -- --clearCache`
3. Check for version mismatches in `package-lock.json`
4. Review test output for specific error messages

### Hot Module Replacement Not Working

**Problem:** Changes not reflected in browser

**Solutions:**
1. Restart dev server: `npm run dev`
2. Clear browser cache
3. Check for syntax errors in code
4. Verify file is saved properly

### Node Version Issues

**Problem:** Errors related to Node.js version

**Solutions:**
1. Check required version in `.nvmrc` and `package.json`
2. Install correct version: `nvm install && nvm use`
3. Verify installation: `node --version`

## Performance Optimization

### Code Splitting

Vite automatically code-splits the application for optimal loading:
- Dynamic imports for route-based splitting
- Vendor chunk separation
- CSS extraction and optimization

### Asset Optimization

- Images and assets are automatically optimized
- Content hashing for cache busting
- Compression-ready output

### Runtime Performance

- React 19 with automatic batching
- Minimal re-renders using proper state management
- Efficient SSE stream handling with cleanup
- Virtualization not needed due to message pagination

## Browser Support

The application targets modern browsers:
- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)

Older browsers may require additional polyfills.

## Dependencies

Key dependencies and their purposes:

- `react` & `react-dom` - UI library
- `lucide-react` - Icon components
- `vite` - Build tool and dev server
- `@vitejs/plugin-react` - React Fast Refresh support
- `tailwindcss` - Utility-first CSS
- `typescript` - Type checking
- `vitest` - Testing framework
- `@testing-library/react` - Component testing utilities
- `eslint` & plugins - Code quality tools

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Related Documentation

- [Root README](../README.md) - Project overview
- [Backend README](../backend/README.md) - Backend setup and API documentation
