package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"wali-payment-service/models"
	"wali-payment-service/providers"
)

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

	c.JSON(http.StatusCreated, response)
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
