package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"bytes"
	"encoding/json"
	"log"

	"wali-payment-service/models"
	"wali-payment-service/providers"
)

const ComplianceServiceURL = "http://localhost:8002/api/v1/compliance/events"

type ComplianceEvent struct {
	EventType     string `json:"event_type"`
	Amount        int    `json:"amount"`
	Currency      string `json:"currency"`
	UserID        string `json:"user_id"`
	PolicyID      string `json:"policy_id"`
	TransactionID string `json:"transaction_id"`
	Provider      string `json:"provider"`
}

type PaymentHandler struct {
	orchestrator *providers.PaymentOrchestrator
}

func NewPaymentHandler(orchestrator *providers.PaymentOrchestrator) *PaymentHandler {
	return &PaymentHandler{
		orchestrator: orchestrator,
	}
}

// POST /api/v1/payments/initiate
func (h *PaymentHandler) InitiatePayment(c *gin.Context) {
	var request models.PaymentRequest

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate request
	if request.Amount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "amount must be positive"})
		return
	}

	if request.Phone == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "phone is required"})
		return
	}

	// Process payment
	response, err := h.orchestrator.ProcessPayment(c.Request.Context(), &request)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Log to Compliance Service (Async or Sync based on requirements)
	// Ideally this should be robust (queue), but direct call for MVP
	go h.logToCompliance(models.PaymentProvider(request.Provider), request, response.TransactionRef)

	c.JSON(http.StatusCreated, response)
}

func (h *PaymentHandler) logToCompliance(provider models.PaymentProvider, req models.PaymentRequest, txID string) {
	event := ComplianceEvent{
		EventType:     "premium_collected", // Assuming all payments are premiums for now
		Amount:        int(req.Amount),
		Currency:      "XOF",
		UserID:        "user-uuid-placeholder", // In real app, get from Context/Auth
		PolicyID:      req.PolicyID,
		TransactionID: txID,
		Provider:      string(provider),
	}

	jsonData, _ := json.Marshal(event)
	resp, err := http.Post(ComplianceServiceURL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Failed to log compliance event: %v", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Compliance service returned non-OK status: %d", resp.StatusCode)
	}
}

// GET /api/v1/payments/verify/:transaction_ref
func (h *PaymentHandler) VerifyPayment(c *gin.Context) {
	transactionRef := c.Param("transaction_ref")
	provider := models.PaymentProvider(c.Query("provider"))

	if provider == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "provider query parameter required"})
		return
	}

	status, err := h.orchestrator.VerifyPayment(c.Request.Context(), transactionRef, provider)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"transaction_ref": transactionRef,
		"provider":        provider,
		"status":          status,
	})
}

// POST /webhooks/orange/payments
func (h *PaymentHandler) OrangeWebhook(c *gin.Context) {
	var payload models.WebhookPayload

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Verify webhook signature
	// TODO: Update transaction status in database
	// TODO: Publish to RabbitMQ for async processing

	c.JSON(http.StatusOK, gin.H{"status": "received"})
}

// POST /webhooks/mtn/collections
func (h *PaymentHandler) MTNWebhook(c *gin.Context) {
	var payload models.WebhookPayload

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Verify webhook signature
	// TODO: Update transaction status
	// TODO: Notify policy service to activate policy

	c.JSON(http.StatusOK, gin.H{"status": "received"})
}

// POST /webhooks/wave/payments
func (h *PaymentHandler) WaveWebhook(c *gin.Context) {
	var payload models.WebhookPayload

	// Get signature from header
	_ = c.GetHeader("X-Wave-Signature")

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// TODO: Verify HMAC signature
	// TODO: Process webhook

	c.JSON(http.StatusOK, gin.H{"status": "received"})
}
