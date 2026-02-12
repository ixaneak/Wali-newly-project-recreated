package config

import (
	"fmt"
	"os"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	// Server
	Port string

	// Database
	DatabaseURL string

	// Redis
	RedisURL string

	//Orange Money
	OrangeClientID     string
	OrangeClientSecret string
	OrangeAPIURL       string
	OrangeMerchantCode string

	// MTN MoMo
	MTNAPIUser         string
	MTNAPIKey          string
	MTNSubscriptionKey string
	MTNTargetEnv       string
	MTNCallbackURL     string

	// Wave
	WaveAPIKey      string
	WaveSecretKey   string
	WaveCheckoutURL string

	// SaaS Platform Config
	DefaultPartnerID         string // Default partner insurer (e.g. NSIA)
	PartnerCollectionAccount string // Partner's payment collection account
	IsSaaSPlatform           bool   // Always true — Wali is a software vendor

	// Testing
	MockPaymentProviders bool

	// Rate Limiting
	RateLimitRequests int
	RateLimitWindow   time.Duration
}

func Load() *Config {
	// Load .env file (try local first, then root)
	_ = godotenv.Load(".env")
	_ = godotenv.Load("../../.env")

	return &Config{
		Port:        getEnv("PORT", "8080"),
		DatabaseURL: getEnv("DATABASE_URL", ""),
		RedisURL:    getEnv("REDIS_URL", "redis://localhost:6379"),

		OrangeClientID:     getEnv("ORANGE_CLIENT_ID", ""),
		OrangeClientSecret: getEnv("ORANGE_CLIENT_SECRET", ""),
		OrangeAPIURL:       getEnv("ORANGE_API_URL", "https://api.orange.com"),
		OrangeMerchantCode: getEnv("ORANGE_MERCHANT_CODE", ""),

		MTNAPIUser:         getEnv("MTN_API_USER", ""),
		MTNAPIKey:          getEnv("MTN_API_KEY", ""),
		MTNSubscriptionKey: getEnv("MTN_SUBSCRIPTION_KEY", ""),
		MTNTargetEnv:       getEnv("MTN_TARGET_ENVIRONMENT", "sandbox"),
		MTNCallbackURL:     getEnv("MTN_CALLBACK_URL", ""),

		WaveAPIKey:      getEnv("WAVE_API_KEY", ""),
		WaveSecretKey:   getEnv("WAVE_SECRET_KEY", ""),
		WaveCheckoutURL: getEnv("WAVE_CHECKOUT_URL", "https://api.wave.com/v1/checkout/sessions"),

		DefaultPartnerID:         getEnv("DEFAULT_PARTNER_ID", "NSIA"),
		PartnerCollectionAccount: getEnv("PARTNER_COLLECTION_ACCOUNT", ""),
		IsSaaSPlatform:           true, // Wali is always a SaaS platform

		// Rate Limiting
		RateLimitRequests: getEnvInt("RATE_LIMIT_REQUESTS", 100),
		RateLimitWindow:   getEnvDuration("RATE_LIMIT_WINDOW_SECONDS", 60),

		MockPaymentProviders: getEnv("MOCK_PAYMENT_PROVIDERS", "false") == "true",
	}
}

func getEnvInt(key string, defaultValue int) int {
	strVal := getEnv(key, "")
	if strVal == "" {
		return defaultValue
	}
	var val int
	fmt.Sscanf(strVal, "%d", &val)
	return val
}

func getEnvDuration(key string, defaultValue int) time.Duration {
	val := getEnvInt(key, defaultValue)
	return time.Duration(val) * time.Second
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
