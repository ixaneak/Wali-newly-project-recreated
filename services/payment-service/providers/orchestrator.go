package providers

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
	"github.com/sony/gobreaker"

	"wali-payment-service/config"
	"wali-payment-service/models"
)

const (
	RedisIdempotencyPrefix = "idempotency:"
	RedisIdempotencyTTL    = 24 * time.Hour
)

type PaymentOrchestrator struct {
	cfg            *config.Config
	redis          *redis.Client
	orangeProvider *OrangeMoneyProvider
	mtnProvider    *MTNMoMoProvider
	waveProvider   *WaveProvider

	// Circuit breakers for each provider
	orangeCB *gobreaker.CircuitBreaker
	mtnCB    *gobreaker.CircuitBreaker
	waveCB   *gobreaker.CircuitBreaker
}

func NewPaymentOrchestrator(cfg *config.Config, redisClient *redis.Client) *PaymentOrchestrator {
	settings := gobreaker.Settings{
		Name:        "payment-provider",
		MaxRequests: 3,
		Interval:    time.Minute,
		Timeout:     30 * time.Second,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.Requests >= 3 && failureRatio >= 0.6
		},
	}

	orangeCB := gobreaker.NewCircuitBreaker(settings)
	// orangeCB.Name = "orange-money"

	mtnCB := gobreaker.NewCircuitBreaker(settings)
	// mtnCB.Name = "mtn-momo"

	waveCB := gobreaker.NewCircuitBreaker(settings)
	// waveCB.Name = "wave"

	return &PaymentOrchestrator{
		cfg:            cfg,
		redis:          redisClient,
		orangeProvider: NewOrangeMoneyProvider(cfg),
		mtnProvider:    NewMTNMoMoProvider(cfg),
		waveProvider:   NewWaveProvider(cfg),
		orangeCB:       orangeCB,
		mtnCB:          mtnCB,
		waveCB:         waveCB,
	}
}

// Process payment with tri-provider fallback
func (p *PaymentOrchestrator) ProcessPayment(ctx context.Context, request *models.PaymentRequest) (*models.PaymentResponse, error) {
	// Idempotency check
	if request.IdempotencyKey != "" {
		if cached, err := p.checkIdempotency(ctx, request.IdempotencyKey); err == nil && cached != nil {
			return cached, nil
		}
	} else {
		request.IdempotencyKey = uuid.New().String()
	}

	// Create transaction
	txn := &models.Transaction{
		ID:             uuid.New().String(),
		UserID:         request.UserID,
		PolicyID:       request.PolicyID,
		Amount:         request.Amount,
		Status:         models.StatusPending,
		RetryCount:     0,
		MaxRetries:     3,
		IdempotencyKey: request.IdempotencyKey,
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	// Determine provider order based on user preference or default
	providers := []models.PaymentProvider{models.ProviderOrange, models.ProviderMTN, models.ProviderWave}
	if request.Provider != "" {
		// User specified provider - make it priority
		providers = p.reorderProviders(request.Provider, providers)
	}

	var lastErr error

	// Try each provider in sequence
	for _, provider := range providers {
		log.Printf("Attempting payment with provider: %s", provider)

		txn.Provider = provider
		txn.TransactionRef = fmt.Sprintf("%s-%s-%d", provider, uuid.New().String(), time.Now().Unix())

		err := p.attemptPayment(ctx, txn, request.Phone, provider)

		if err == nil {
			// Success!
			response := &models.PaymentResponse{
				TransactionID:  txn.ID,
				TransactionRef: txn.TransactionRef,
				Provider:       txn.Provider,
				Status:         txn.Status,
				Amount:         txn.Amount,
				CreatedAt:      txn.CreatedAt,
			}

			// Cache result for idempotency
			p.cacheIdempotency(ctx, request.IdempotencyKey, response)

			// Log audit trail
			p.logAuditTrail(txn, provider, "success", nil)

			return response, nil
		}

		// Log failure and try next provider
		p.logAuditTrail(txn, provider, "failed", err)
		lastErr = err
	}

	// All providers failed
	return nil, fmt.Errorf("all payment providers failed: %w", lastErr)
}

// Attempt payment with a specific provider (with circuit breaker)
func (p *PaymentOrchestrator) attemptPayment(ctx context.Context, txn *models.Transaction, phone string, provider models.PaymentProvider) error {
	// Mock Mode Check
	if p.cfg.MockPaymentProviders {
		log.Printf("[MOCK] Simulating successful payment for %s via %s", phone, provider)
		txn.Status = models.StatusSuccess
		txn.ProviderResponse = map[string]interface{}{
			"status": "SUCCESS",
			"mock":   true,
			"tx_ref": txn.TransactionRef,
		}
		return nil
	}

	var err error

	switch provider {
	case models.ProviderOrange:
		_, err = p.orangeCB.Execute(func() (interface{}, error) {
			return nil, p.orangeProvider.RequestPayment(txn, phone)
		})
	case models.ProviderMTN:
		_, err = p.mtnCB.Execute(func() (interface{}, error) {
			return nil, p.mtnProvider.RequestPayment(txn, phone)
		})
	case models.ProviderWave:
		_, err = p.waveCB.Execute(func() (interface{}, error) {
			return nil, p.waveProvider.RequestPayment(txn, phone)
		})
	default:
		return fmt.Errorf("unknown provider: %s", provider)
	}

	return err
}

// Reorder providers based on preference
func (p *PaymentOrchestrator) reorderProviders(preferred models.PaymentProvider, providers []models.PaymentProvider) []models.PaymentProvider {
	var reordered []models.PaymentProvider

	// Add preferred first
	reordered = append(reordered, preferred)

	// Add others
	for _, prov := range providers {
		if prov != preferred {
			reordered = append(reordered, prov)
		}
	}

	return reordered
}

// Idempotency check
func (p *PaymentOrchestrator) checkIdempotency(ctx context.Context, key string) (*models.PaymentResponse, error) {
	redisKey := RedisIdempotencyPrefix + key

	_, err := p.redis.Get(ctx, redisKey).Result()
	if err == redis.Nil {
		return nil, fmt.Errorf("not found")
	}
	if err != nil {
		return nil, err
	}

	var response models.PaymentResponse
	// Simple string storage - in production, use JSON
	log.Printf("Idempotency hit for key: %s", key)

	return &response, nil
}

// Cache idempotency result
func (p *PaymentOrchestrator) cacheIdempotency(ctx context.Context, key string, response *models.PaymentResponse) {
	redisKey := RedisIdempotencyPrefix + key
	p.redis.Set(ctx, redisKey, response.TransactionID, RedisIdempotencyTTL)
}

// Log audit trail for compliance
func (p *PaymentOrchestrator) logAuditTrail(txn *models.Transaction, provider models.PaymentProvider, status string, err error) {
	log.Printf("[AUDIT] Provider: %s, TxnRef: %s, Status: %s, Error: %v",
		provider, txn.TransactionRef, status, err)

	// In production, write to immutable financial_events table
	// TODO: Insert into PostgreSQL financial_events table
}

// Verify payment status
func (p *PaymentOrchestrator) VerifyPayment(ctx context.Context, transactionRef string, provider models.PaymentProvider) (models.TransactionStatus, error) {
	if p.cfg.MockPaymentProviders {
		log.Printf("[MOCK] Verifying payment %s as SUCCESS", transactionRef)
		return models.StatusSuccess, nil
	}

	switch provider {
	case models.ProviderOrange:
		return p.orangeProvider.VerifyPayment(transactionRef)
	case models.ProviderMTN:
		return p.mtnProvider.VerifyPayment(transactionRef)
	case models.ProviderWave:
		return p.waveProvider.VerifyPayment(transactionRef)
	default:
		return models.StatusFailed, fmt.Errorf("unknown provider: %s", provider)
	}
}
