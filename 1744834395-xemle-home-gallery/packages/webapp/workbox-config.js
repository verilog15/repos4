module.exports = {
  globDirectory: "dist",
  globPatterns: [
    "**/*.{html,css,js,png,svg,eot,ttf,woff,woff2,webmanifest}"
  ],
  swDest: "dist/service-worker.js",
  clientsClaim: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /\.(html|js|css|webmanifest)$/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'assets',
        expiration: {
          maxEntries: 10,
          maxAgeSeconds: 24 * 60 * 60 // 1 day
        },
        fetchOptions: {
          credentials: 'same-origin'
        },
      },
    },
    {
      urlPattern: /\.(png|svg|eot|ttf|woff|woff2)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'fonts',
        expiration: {
          maxEntries: 15,
          maxAgeSeconds: 7 * 24 * 60 * 60 // 1 week
        },
        fetchOptions: {
          credentials: 'same-origin'
        },
      },
    },
    {
      urlPattern: /-preview-320\.jpg$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'images',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 14 * 24 * 60 * 60 // 2 weeks
        },
        fetchOptions: {
          credentials: 'same-origin'
        },
      },
    }],

};