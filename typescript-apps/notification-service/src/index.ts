import express, { Application, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { config } from './config';
import notificationRoutes from './routes/notifications';
import { logger } from './utils/logger';

const app: Application = express();

// Middleware
app.use(helmet());
app.use(cors({
    origin: config.allowedOrigins,
    credentials: true,
}));
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/v1/notifications', notificationRoutes);

// Health check
app.get('/health', (req: Request, res: Response) => {
    res.json({
        status: 'healthy',
        service: 'notification-service',
        timestamp: new Date().toISOString(),
    });
});

// Root endpoint
app.get('/', (req: Request, res: Response) => {
    res.json({
        service: 'Wali Notification Service',
        version: '1.0.0',
        endpoints: {
            health: '/health',
            otpGenerate: 'POST /api/v1/notifications/otp/generate',
            otpVerify: 'POST /api/v1/notifications/otp/verify',
            sendNotification: 'POST /api/v1/notifications/send',
        },
    });
});

// Error handling
app.use((err: Error, req: Request, res: Response, next: any) => {
    logger.error('Unhandled error:', err);
    res.status(500).json({
        success: false,
        message: 'Internal server error',
    });
});

// Start server
const PORT = config.port;
app.listen(PORT, () => {
    logger.info(`Notification Service running on port ${PORT}`);
    logger.info(`Environment: ${config.nodeEnv}`);
});

export default app;
