import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const path = request.nextUrl.pathname;

    // 1. Protect Admin Routes
    if (path.startsWith('/admin')) {
        // Allow public admin routes (login page)
        if (path === '/admin' || path === '/admin/login') {
            // If user already has token, redirect to dashboard
            const token = request.cookies.get('wali_auth_token')?.value;
            if (token) {
                return NextResponse.redirect(new URL('/admin/dash', request.url));
            }
            return NextResponse.next();
        }

        // Check for auth token in cookies for all other admin routes
        const token = request.cookies.get('wali_auth_token')?.value;

        if (!token) {
            // Redirect to login if no token
            return NextResponse.redirect(new URL('/admin', request.url));
        }

        // Token exists - middleware can't validate JWT signature without JWT secret
        // The API calls will validate the token and redirect if invalid
        // We just check presence here for UX speed
    }

    // 2. Protect User Dashboard Routes (optional - can be handled client-side for PWA)
    if (path.startsWith('/dashboard')) {
        // For PWA, we typically use localStorage which middleware can't access
        // If you want cookie-based auth for dashboard, implement similar to admin
        const token = request.cookies.get('wali_user_token')?.value;
        
        // Allow access if token exists (validation happens in API)
        if (!token && path !== '/dashboard/login') {
            // Uncomment to enforce auth on dashboard
            // return NextResponse.redirect(new URL('/login', request.url));
        }
    }

    // 3. Protect Pharmacy Admin Routes
    if (path.startsWith('/pharmacy')) {
        // Public routes
        if (path === '/pharmacy/login' || path === '/pharmacy/register') {
            return NextResponse.next();
        }

        // Check for pharmacy auth
        const token = request.cookies.get('pharmacy_token')?.value;
        
        if (!token && path !== '/pharmacy/login') {
            return NextResponse.redirect(new URL('/pharmacy/login', request.url));
        }
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        '/admin/:path*',
        '/dashboard/:path*',
        '/pharmacy/:path*',
    ],
};
