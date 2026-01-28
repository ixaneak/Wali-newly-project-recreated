package models

import (
	"context"
	"time"
)

// PaymentRepository defines the data access layer for payments
type PaymentRepository interface {
	// Idempotency
	GetIdempotency(ctx context.Context, key string) (*PaymentResponse, error)
	SaveIdempotency(ctx context.Context, key string, response *PaymentResponse, ttl time.Duration) error

	// Transaction Management
	SaveTransaction(ctx context.Context, txn *Transaction) error
	GetTransactionByRef(ctx context.Context, ref string) (*Transaction, error)
	UpdateTransactionStatus(ctx context.Context, id string, status TransactionStatus) error
}
