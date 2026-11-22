/* externalDir lets the demo import the sections from ../components.
   BUILD_DIR lets a test build run without touching the dev server's .next folder. */
const nextConfig = {
  experimental: { externalDir: true },
  distDir: process.env.BUILD_DIR || ".next",
};

export default nextConfig;
