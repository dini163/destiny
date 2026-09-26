import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// 测试放 tests/ 而不是 src/：src/** 保持只装运行代码，`vite build` 的产物不受测件影响。
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.{ts,tsx}'],
    setupFiles: ['tests/setup.ts'],
  },
});
