import { logger } from '../utils/logger';

export class MockRedisClient {
    private store: Map<string, { value: string; expiry: number }> = new Map();

    constructor() {
        logger.info('Using Mock Redis Client (In-Memory)');
    }

    async connect(): Promise<void> {
        logger.info('Mock Redis Client connected');
    }

    on(event: string, callback: (...args: any[]) => void): void {
        // No-op for mock
    }

    async get(key: string): Promise<string | null> {
        const item = this.store.get(key);
        if (!item) return null;

        if (Date.now() > item.expiry) {
            this.store.delete(key);
            return null;
        }

        return item.value;
    }

    async setEx(key: string, seconds: number, value: string): Promise<string> {
        this.store.set(key, {
            value,
            expiry: Date.now() + seconds * 1000,
        });
        return 'OK';
    }

    async del(key: string): Promise<number> {
        return this.store.delete(key) ? 1 : 0;
    }

    async exists(key: string): Promise<number> {
        const item = await this.get(key); // Check expiry
        return item ? 1 : 0;
    }

    async ttl(key: string): Promise<number> {
        const item = this.store.get(key);
        if (!item) return -2; // Key does not exist

        const now = Date.now();
        if (now > item.expiry) {
            this.store.delete(key);
            return -2;
        }

        return Math.ceil((item.expiry - now) / 1000);
    }
}
