package models

import (
	"time"
)

type PaymentProvider string

const (
	ProviderOrange PaymentProvider = "orange"
	ProviderMTN    PaymentProvider = "mtn"
	ProviderWave   PaymentProvider = "wave"
)

type TransactionStatus string

const (
	StatusPending  TransactionStatus = "pending"
	StatusSuccess  TransactionStatus = "success"
	StatusFailed   TransactionStatus = "failed"
	StatusRefunded TransactionStatus = "refunded"
)

type PaymentRequest struct {
	UserID           string          `json:"user_id"`
	PolicyID         string          `json:"policy_id"`
	Amount           int             `json:"amount"` // XOF as integer
	Phone            string          `json:"phone"`
	Provider         PaymentProvider `json:"provider,omitempty"`
	IdempotencyKey   string          `json:"idempotency_key,omitempty"`
}

type PaymentResponse struct {
	TransactionID    string            `json:"transaction_id"`
	TransactionRef   string            `json:"transaction_ref"`
	Provider         PaymentProvider   `json:"provider"`
	Status           TransactionStatus `json:"status"`
	Amount           int               `json:"amount"`
	CreatedAt        time.Time         `json:"created_at"`
}

type Transaction struct {
	ID               string            `json:"id"`
	UserID           string            `json:"user_id"`
	PolicyID         string            `json:"policy_id,omitempty"`
	Provider         PaymentProvider   `json:"provider"`
	TransactionRef   string            `json:"transaction_ref"`
	Amount           int               `json:"amount"`
	Status           TransactionStatus `json:"status"`
	RetryCount       int               `json:"retry_count"`
	MaxRetries       int               `json:"max_retries"`
	IdempotencyKey   string            `json:"idempotency_key"`
	ProviderResponse map[string]interface{} `json:"provider_response,omitempty"`
	ErrorMessage     string            `json:"error_message,omitempty"`
	CreatedAt        time.Time         `json:"created_at"`
	UpdatedAt        time.Time         `json:"updated_at"`
	CompletedAt      *time.Time        `json:"completed_at,omitempty"`
}

type WebhookPayload struct {
	Provider         PaymentProvider   `json:"provider"`
	TransactionRef   string            `json:"transaction_ref"`
	Status           TransactionStatus `json:"status"`
	Amount           int               `json:"amount"`
	Metadata         map[string]interface{} `json:"metadata"`
	Signature        string            `json:"signature,omitempty"`
}
