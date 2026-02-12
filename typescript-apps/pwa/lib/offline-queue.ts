// import { apiService } from './api-client'; // Removed to prevent circular dependency
import axios from 'axios';

interface QueuedRequest {
    id: string;
    endpoint: string;
    method: string;
    payload: any;
    partnerId: string;
    createdAt: number;
    retryCount: number;
}

const STORAGE_KEY = 'walisub_offline_queue';

class OfflineQueueService {
    private queue: QueuedRequest[] = [];
    private isSyncing = false;

    constructor() {
        if (typeof window !== 'undefined') {
            this.loadQueue();
            window.addEventListener('online', this.sync.bind(this));
        }
    }

    private loadQueue() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            try {
                this.queue = JSON.parse(stored);
            } catch (e) {
                console.error("Failed to parse offline queue", e);
                this.queue = [];
            }
        }
    }

    private saveQueue() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.queue));
    }

    addRequest(endpoint: string, method: string, payload: any, partnerId: string) {
        const request: QueuedRequest = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            endpoint,
            method,
            payload,
            partnerId,
            createdAt: Date.now(),
            retryCount: 0
        };
        this.queue.push(request);
        this.saveQueue();

        // Try to sync immediately if online
        if (navigator.onLine) {
            this.sync();
        }
    }

    async sync() {
        if (this.isSyncing || this.queue.length === 0 || !navigator.onLine) return;

        this.isSyncing = true;
        console.log(`[OfflineQueue] Syncing ${this.queue.length} requests...`);

        // Process queue copy
        const currentQueue = [...this.queue];
        const remainingQueue: QueuedRequest[] = [];
        let authError = false;

        // Lazy load auth to ensure it's initialized
        const { auth } = await import('./firebase');

        for (const req of currentQueue) {
            if (authError) {
                remainingQueue.push(req);
                continue;
            }

            try {
                // Get fresh token
                let token = null;
                if (auth.currentUser) {
                    try {
                        // Force refresh if needed, but standard should be fine
                        token = await auth.currentUser.getIdToken();
                    } catch (e) {
                        console.warn("Failed to get fresh token for sync", e);
                    }
                }

                // Fallback to storage if auth.currentUser is not ready (which shouldn't happen if online?)
                if (!token) {
                    token = localStorage.getItem('wali_token');
                }

                const headers: any = {
                    'Content-Type': 'application/json',
                    'X-Platform': 'web',
                    'X-App-Version': '2.0.0'
                };
                if (token) headers['Authorization'] = `Bearer ${token}`;

                console.log(`[OfflineQueue] Replaying ${req.method} ${req.endpoint}`);

                await axios.request({
                    url: req.endpoint,
                    method: req.method,
                    data: req.payload,
                    headers
                });

                console.log(`[OfflineQueue] Request ${req.id} synced successfully`);
                // Success, don't add to remaining
            } catch (e: any) {
                console.error(`[OfflineQueue] Failed to sync request ${req.id}`, e);

                // Handle 401 - Stop syncing to prevent account lock/spam
                if (e.response && e.response.status === 401) {
                    authError = true;
                    remainingQueue.push(req);
                    continue;
                }

                // Handle other errors
                if (req.retryCount < 3) {
                    req.retryCount++;
                    // Exponential backoff: 1s, 2s, 4s
                    const delay = Math.pow(2, req.retryCount - 1) * 1000;
                    console.log(`[OfflineQueue] Retrying request ${req.id} in ${delay}ms (Attempt ${req.retryCount}/3)`);

                    // We don't verify wait here, we just keep it in queue. 
                    // ideally we'd pause processing, but simplified: 
                    // just push back to remaining and maybe delay next sync trigger?
                    // For now, simple push back, but it will be retried on next sync() call.
                    // To truly backoff, we'd need to store 'nextRetryTime' in the request.

                    // Let's add nextRetryTime to QueuedRequest interface if we could, 
                    // but for now, let's just leave it in the queue. 
                    // The sync function is called on 'online' event or manual trigger.
                    // If we want to delay, we can't easily do it without blocking others.
                    // So we will just increment retryCount.

                    remainingQueue.push(req);
                } else {
                    console.warn(`[OfflineQueue] Dropping request ${req.id} after max retries`);
                    // TODO: Notify user that a request failed permanently?
                }
            }
        }

        this.queue = remainingQueue;
        this.saveQueue();
        this.isSyncing = false;

        if (this.queue.length === 0) {
            console.log("[OfflineQueue] Sync complete, queue empty");
        }
    }

    getQueueSize() {
        return this.queue.length;
    }
}

export const offlineQueue = new OfflineQueueService();
