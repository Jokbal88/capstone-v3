/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html',
    '../**/templates/**/*.html',
    '../**/forms.py',
    '../**/models.py',
    '../**/views.py',
    '../**/urls.py',
    './templates/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
} 