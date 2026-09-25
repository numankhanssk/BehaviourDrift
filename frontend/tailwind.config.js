/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        bg: '#09090F',
        panelSolid: '#12121C',
        border: 'rgba(255,255,255,0.09)',
        borderStrong: 'rgba(255,255,255,0.16)',
        textHi: '#F3F3F7',
        textLo: '#8B8B9A',
        violet: '#8B5CF6',
        cyan: '#22D3EE',
        danger: '#F0466B',
        success: '#34D399',
        neutral: '#6B7280',
      },
      backgroundImage: {
        'bd-gradient': 'linear-gradient(135deg, #8B5CF6 0%, #22D3EE 100%)',
        'bd-glow': `radial-gradient(ellipse 900px 500px at 12% -8%, rgba(139,92,246,0.16), transparent 60%),
                    radial-gradient(ellipse 800px 600px at 100% 15%, rgba(34,211,238,0.10), transparent 55%)`,
      },
    },
  },
  plugins: [],
}
