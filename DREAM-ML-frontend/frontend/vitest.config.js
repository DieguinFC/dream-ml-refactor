// Test configuration, kept separate so vite.config.js (dev server and build) does not change.
// Tests live in tests/, outside src/, because sonar.sources includes src/ and the Sonar
// exclusions are frozen for the before/after comparison.
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    include: ['tests/**/*.test.{js,jsx}'],
    setupFiles: ['./tests/setup.js'],
    coverage: {
      provider: 'v8',
      // Count executable lines the way Istanbul does; plain v8 counts every source line,
      // which made frontend lines-to-cover about six times larger than Sonar's own count.
      experimentalAstAwareRemapping: true,
      // Report only files the tests load. Sonar computes the other files' executable lines
      // itself, as it did for the baseline, so project coverage stays comparable.
      all: false,
      include: ['src/**/*.{js,jsx}'],
      reporter: ['text-summary', 'lcov'],
      reportsDirectory: 'coverage',
    },
  },
});
