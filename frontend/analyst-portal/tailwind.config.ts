import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        severity: {
          critical: '#DC2626',
          high: '#EA580C',
          medium: '#CA8A04',
          low: '#2563EB',
          info: '#6B7280',
        },
        verdict: {
          tp: '#DC2626',
          fp: '#16A34A',
          dup: '#9333EA',
          retest: '#CA8A04',
        },
      },
    },
  },
  plugins: [],
};

export default config;
