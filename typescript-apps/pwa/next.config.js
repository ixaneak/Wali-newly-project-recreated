const withPWA = require("@ducanh2912/next-pwa").default({
    dest: "public",
    disable: process.env.NODE_ENV === "development",
    register: true,
    skipWaiting: true,
});

/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: false,
    poweredByHeader: false,
    output: 'standalone',
    async rewrites() {
        return [
            {
                source: '/api/v1/policy/:path*',
                destination: 'http://localhost:8000/api/v1/:path*',
            },
            {
                source: '/api/v1/users/:path*',
                destination: 'http://localhost:8000/api/v1/users/:path*',
            },
            {
                source: '/api/v1/claims/:path*',
                destination: 'http://localhost:8000/api/v1/claims/:path*',
            },
            {
                source: '/api/v1/photos/:path*',
                destination: 'http://localhost:8000/api/v1/photos/:path*',
            },
            {
                source: '/api/v1/compliance/:path*',
                destination: 'http://localhost:8000/api/v1/compliance/:path*',
            },
            {
                source: '/api/v1/payments/:path*',
                destination: 'http://localhost:8080/api/v1/payments/:path*',
            },
            {
                source: '/api/v1/notifications/:path*',
                destination: 'http://localhost:8003/api/v1/notifications/:path*',
            },
        ]
    },
}

// module.exports = withPWA(nextConfig)
module.exports = nextConfig
