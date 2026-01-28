package providers

import (
	"context"
	"errors"
	"sync"
	"time"

	"wali-payment-service/models"
)

// InMemoryRepository implements PaymentRepository using maps
type InMemoryRepository struct {
	transactions    map[string]*models.Transaction
	idempotencyKeys map[string]idempotencyRecord
	mu              sync.RWMutex
}

type idempotencyRecord struct {
	response  *models.PaymentResponse
	expiresAt time.Time
}

// NewInMemoryRepository creates a new instance
func NewInMemoryRepository() *InMemoryRepository {
	return &InMemoryRepository{
		transactions:    make(map[string]*models.Transaction),
		idempotencyKeys: make(map[string]idempotencyRecord),
	}
}

// GetIdempotency retrieves a cached response
func (r *InMemoryRepository) GetIdempotency(ctx context.Context, key string) (*models.PaymentResponse, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	record, exists := r.idempotencyKeys[key]
	if !exists {
		return nil, errors.New("not found")
	}

	if time.Now().After(record.expiresAt) {
		return nil, errors.New("expired")
	}

	return record.response, nil
}

// SaveIdempotency caches a response
func (r *InMemoryRepository) SaveIdempotency(ctx context.Context, key string, response *models.PaymentResponse, ttl time.Duration) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.idempotencyKeys[key] = idempotencyRecord{
		response:  response,
		expiresAt: time.Now().Add(ttl),
	}
	return nil
}

// SaveTransaction saves a transaction
func (r *InMemoryRepository) SaveTransaction(ctx context.Context, txn *models.Transaction) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Store a copy to prevent external modification issues in a real app (though less robust for in-mem pointers)
	// For simplicity, we store the pointer, but in a real DB it's serialized.
	r.transactions[txn.ID] = txn
	return nil
}

// GetTransactionByRef finds a transaction by reference
func (r *InMemoryRepository) GetTransactionByRef(ctx context.Context, ref string) (*models.Transaction, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	for _, txn := range r.transactions {
		if txn.TransactionRef == ref {
			return txn, nil
		}
	}
	return nil, errors.New("transaction not found")
}

// UpdateTransactionStatus updates the status
func (r *InMemoryRepository) UpdateTransactionStatus(ctx context.Context, id string, status models.TransactionStatus) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	txn, exists := r.transactions[id]
	if !exists {
		return errors.New("transaction not found")
	}

	txn.Status = status
	txn.UpdatedAt = time.Now()
	return nil
}
