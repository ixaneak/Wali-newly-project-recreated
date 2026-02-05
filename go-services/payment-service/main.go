package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"

	"wali-payment-service/config"
	"wali-payment-service/handlers"
	"wali-payment-service/middleware"
	"wali-payment-service/models"
	"wali-payment-service/providers"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Initialize Redis and Repository
	var repo models.PaymentRepository
	ctx := context.Background()

	opt, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		log.Printf("Warning: Failed to parse Redis URL: %v", err)
	}

	redisClient := redis.NewClient(opt)

	// Test Redis connection
	// Check connection or mock flag
	if err := redisClient.Ping(ctx).Err(); err != nil || cfg.MockPaymentProviders {
		if cfg.MockPaymentProviders {
			log.Println("ℹ️ Mock mode enabled via config")
		} else {
			log.Printf("Warning: Redis connection failed: %v", err)
		}
		log.Println("⚠️ Using InMemoryRepository")
		repo = providers.NewInMemoryRepository()
	} else {
		log.Println("✓ Redis connected")
		repo = providers.NewRedisRepository(redisClient)
	}

	// Initialize payment orchestrator
	orchestrator := providers.NewPaymentOrchestrator(cfg, repo)
	log.Println("✓ Payment orchestrator initialized")

	// Initialize handlers
	paymentHandler := handlers.NewPaymentHandler(orchestrator)

	// Setup Gin router
	if cfg.Port == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.Default()

	// CORS Configuration
	router.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"service":   "payment-service",
			"providers": []string{"orange", "mtn", "wave"},
		})
	})

	// API routes (protected with JWT)
	api := router.Group("/api/v1")
	api.Use(middleware.JWTAuthMiddleware())
	api.Use(middleware.RateLimitMiddleware(cfg, repo))
	{
		payments := api.Group("/payments")
		{
			payments.POST("/initiate", paymentHandler.InitiatePayment)
			payments.GET("/verify/:transaction_ref", paymentHandler.VerifyPayment)
		}
	}

	// Webhook routes
	webhooks := router.Group("/webhooks")
	{
		webhooks.POST("/orange/payments", paymentHandler.OrangeWebhook)
		webhooks.POST("/mtn/collections", paymentHandler.MTNWebhook)
		webhooks.POST("/wave/payments", paymentHandler.WaveWebhook)
	}

	// Start server
	port := cfg.Port
	if port == "" {
		port = "8080"
	}

	server := &http.Server{
		Addr:           fmt.Sprintf(":%s", port),
		Handler:        router,
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	log.Printf("🚀 Wali Payment Service starting on port %s", port)
	log.Printf("📡 Webhooks: /webhooks/orange/payments, /webhooks/mtn/collections, /webhooks/wave/payments")

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Failed to start server: %v", err)
	}
}
