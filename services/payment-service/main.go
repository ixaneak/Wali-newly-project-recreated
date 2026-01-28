package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"
	
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	
	"wali-payment-service/config"
	"wali-payment-service/handlers"
	"wali-payment-service/providers"
)

func main() {
	// Load configuration
	cfg := config.Load()
	
	// Initialize Redis
	opt, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		log.Fatalf("Failed to parse Redis URL: %v", err)
	}
	
	redisClient := redis.NewClient(opt)
	ctx := context.Background()
	
	// Test Redis connection
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Printf("Warning: Redis connection failed: %v", err)
	} else {
		log.Println("✓ Redis connected")
	}
	
	// Initialize payment orchestrator
	orchestrator := providers.NewPaymentOrchestrator(cfg, redisClient)
	log.Println("✓ Payment orchestrator initialized")
	
	// Initialize handlers
	paymentHandler := handlers.NewPaymentHandler(orchestrator)
	
	// Setup Gin router
	if cfg.Port == "production" {
		gin.SetMode(gin.ReleaseMode)
	}
	
	router := gin.Default()
	
	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "healthy",
			"service": "payment-service",
			"providers": []string{"orange", "mtn", "wave"},
		})
	})
	
	// API routes
	api := router.Group("/api/v1")
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
