package providers

import (
	"context"
	"encoding/json"
	"time"

	"wali-payment-service/models"

	"github.com/go-redis/redis/v8"
)

// RedisRepository implements PaymentRepository using Redis
type RedisRepository struct {
	client *redis.Client
}

// NewRedisRepository creates a new instance
func NewRedisRepository(client *redis.Client) *RedisRepository {
	return &RedisRepository{
		client: client,
	}
}

// GetIdempotency retrieving cached response
func (r *RedisRepository) GetIdempotency(ctx context.Context, key string) (*models.PaymentResponse, error) {
	redisKey := RedisIdempotencyPrefix + key
	val, err := r.client.Get(ctx, redisKey).Result()
	if err != nil {
		return nil, err
	}

	var response models.PaymentResponse
	if err := json.Unmarshal([]byte(val), &response); err != nil {
		return nil, err
	}

	return &response, nil
}

// SaveIdempotency caches a response
func (r *RedisRepository) SaveIdempotency(ctx context.Context, key string, response *models.PaymentResponse, ttl time.Duration) error {
	redisKey := RedisIdempotencyPrefix + key

	bytes, err := json.Marshal(response)
	if err != nil {
		return err
	}

	return r.client.Set(ctx, redisKey, bytes, ttl).Err()
}

// SaveTransaction saves a transaction (No-op/Log for Redis implementation if no DB)
// In a real scenario, this would write to Postgres.
// For now, we can perhaps store it in Redis for short-term visibility or just log it.
func (r *RedisRepository) SaveTransaction(ctx context.Context, txn *models.Transaction) error {
	// Simple Redis storage for visibility (optional)
	// key := "txn:" + txn.ID
	// bytes, _ := json.Marshal(txn)
	// r.client.Set(ctx, key, bytes, 24*time.Hour)
	return nil
}

// GetTransactionByRef finds a transaction
func (r *RedisRepository) GetTransactionByRef(ctx context.Context, ref string) (*models.Transaction, error) {
	// Not implemented for pure Redis without secondary indexing
	return nil, redis.Nil
}

// UpdateTransactionStatus updates the status
func (r *RedisRepository) UpdateTransactionStatus(ctx context.Context, id string, status models.TransactionStatus) error {
	// No-op without DB
	return nil
}

// IncrementRateLimit increments key count and sets expiry
func (r *RedisRepository) IncrementRateLimit(ctx context.Context, key string, window time.Duration) (int64, error) {
	pipe := r.client.Pipeline()
	incr := pipe.Incr(ctx, key)
	pipe.Expire(ctx, key, window)
	_, err := pipe.Exec(ctx)
	if err != nil {
		return 0, err
	}
	return incr.Val(), nil
}
