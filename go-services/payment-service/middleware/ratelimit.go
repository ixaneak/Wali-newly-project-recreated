package middleware

import (
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"wali-payment-service/config"
	"wali-payment-service/models"
)

// RateLimitMiddleware implements a distributed rate limiter using the repository
func RateLimitMiddleware(cfg *config.Config, repo models.PaymentRepository) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Skip for health check or public routes if needed, but here we apply to /api/v1
		// We identify user by UserID from JWT (set by JWTAuthMiddleware)
		// Or fall back to IP if not authenticated yet (though this middleware is usually applied AFTER auth)

		var key string
		userID, exists := c.Get("user_id") // Matches JWTAuthMiddleware
		if exists {
			key = fmt.Sprintf("ratelimit:user:%s", userID)
		} else {
			// Fallback to IP
			key = fmt.Sprintf("ratelimit:ip:%s", c.ClientIP())
		}

		limit := int64(cfg.RateLimitRequests)
		window := cfg.RateLimitWindow

		count, err := repo.IncrementRateLimit(c.Request.Context(), key, window)
		if err != nil {
			// In case of Redis error, we typically allow traffic (fail open) or log error
			// For high security, fail closed. For availability, fail open.
			// Currently failing open but logging.
			fmt.Printf("Rate limit error: %v\n", err)
			c.Next()
			return
		}

		remaining := limit - count
		if remaining < 0 {
			remaining = 0
		}

		resetTime := time.Now().Add(window).Unix() // Approximation for sliding window expiry

		c.Header("X-RateLimit-Limit", fmt.Sprintf("%d", limit))
		c.Header("X-RateLimit-Remaining", fmt.Sprintf("%d", remaining))
		c.Header("X-RateLimit-Reset", fmt.Sprintf("%d", resetTime))

		if count > limit {
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"error": "Too many requests. Please try again later.",
			})
			return
		}

		c.Next()
	}
}
