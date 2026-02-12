package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"

	"wali-payment-service/models"
	"wali-payment-service/providers"
)

const ComplianceServiceURL = "http://localhost:8001/api/v1/compliance/events"

// ComplianceEvent — SaaS model: payments are ROUTED to partner, not collected.
type ComplianceEvent struct {
	EventType      string `json:"event_type"`
	Amount         int    `json:"amount"`
	Currency       string `json:"currency"`
	UserID         string `json:"user_id"`
	SubscriptionID string `json:"subscription_id"` // was: policy_id
	PartnerID      string `json:"partner_id"`       // Which insurer gets the money
	TransactionID  string `json:"transaction_id"`
	Provider       string `json:"provider"`
}

type PaymentHandler struct {
	orchestrator *providers.PaymentOrchestrator
}

func NewPaymentHandler(orchestrator *providers.PaymentOrchestrator) *PaymentHandler {
	return &PaymentHandler{
		orchestrator: orchestrator,
	}
}

// POST /api/v1/partners/{partner_id}/payments/route
// Routes artisan payment to partner insurer. Wali = technology provider.
func (h *PaymentHandler) InitiatePayment(c *gin.Context) {
	var request models.PaymentRequest

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if request.Amount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "amount must be positive"})
		return
	}

	if request.Phone == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "phone is required"})
		return
	}

	// Route payment to partner insurer
	response, err := h.orchestrator.ProcessPayment(c.Request.Context(), &request)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Log payment routing to compliance (not premium collection)
	go h.logPaymentRouting(models.PaymentProvider(request.Provider), request, response.TransactionRef)

	c.JSON(http.StatusCreated, gin.H{
		"transaction_ref": response.TransactionRef,
		"status":          response.Status,
		"wali_role":       "technology_provider",
		"routed_to":       request.PartnerID,
	})
}

// logPaymentRouting logs payment as ROUTED to partner insurer (not collected by Wali).
func (h *PaymentHandler) logPaymentRouting(provider models.PaymentProvider, req models.PaymentRequest, txID string) {
	partnerID := req.PartnerID
	if partnerID == "" {
		partnerID = "NSIA" // Default partner
	}

	event := ComplianceEvent{
		EventType:      "payment_routed", // NOT "premium_collected"
		Amount:         int(req.Amount),
		Currency:       "XOF",
		UserID:         "user-uuid-placeholder",
		SubscriptionID: req.PolicyID,      // Legacy field name in PaymentRequest
		PartnerID:      partnerID,
		TransactionID:  txID,
		Provider:       string(provider),
	}

	jsonData, _ := json.Marshal(event)
	resp, err := http.Post(ComplianceServiceURL, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Failed to log payment routing event: %v", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Compliance service returned non-OK status: %d", resp.StatusCode)
	} else {
		log.Printf("Payment ROUTED to %s: %d XOF via %s. Wali role: technology_provider",
			partnerID, req.Amount, provider)
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
		"wali_role":       "technology_provider",
	})
}

// POST /webhooks/orange/payments
func (h *PaymentHandler) OrangeWebhook(c *gin.Context) {
	var payload struct {
		Status        string `json:"status"`
		TransactionID string `json:"transaction_id"`
		Reference     string `json:"reference"`
		Amount        int    `json:"amount"`
		Currency      string `json:"currency"`
	}

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	log.Printf("Orange webhook: status=%s, ref=%s, amount=%d",
		payload.Status, payload.Reference, payload.Amount)

	// Log as ROUTED, not COLLECTED
	go h.logPaymentRouting(models.ProviderOrange, models.PaymentRequest{
		Amount:   payload.Amount,
		PolicyID: "",
	}, payload.Reference)

	// Confirm enrollment with partner (was: activate policy)
	if payload.Status == "SUCCESS" {
		go h.confirmEnrollment(payload.Reference)
		log.Printf("Payment routed successfully, confirming enrollment: %s", payload.Reference)
	}

	c.JSON(http.StatusOK, gin.H{
		"status":    "received",
		"message":   "Payment routing confirmed",
		"wali_role": "technology_provider",
	})
}

// confirmEnrollment calls the platform service to confirm enrollment after payment routing.
func (h *PaymentHandler) confirmEnrollment(transactionRef string) {
	txn, err := h.orchestrator.GetTransaction(context.Background(), transactionRef)
	if err != nil {
		log.Printf("Failed to find transaction for enrollment confirmation: %v", err)
		return
	}

	if txn.PolicyID == "" {
		log.Printf("Transaction %s has no SubscriptionID, cannot confirm enrollment", transactionRef)
		return
	}

	// Updated URL: /partners/NSIA/enrollments/{id}/confirm
	enrollmentURL := fmt.Sprintf(
		"http://localhost:8000/api/v1/partners/NSIA/enrollments/%s/confirm",
		txn.PolicyID,
	)

	payload := map[string]string{
		"transaction_ref": transactionRef,
	}

	jsonData, _ := json.Marshal(payload)

	req, err := http.NewRequest("POST", enrollmentURL, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Failed to create enrollment confirmation request: %v", err)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("Failed to confirm enrollment: %v", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		log.Printf("Enrollment confirmed for transaction: %s (routed to NSIA)", transactionRef)
	} else {
		bodyBytes, _ := io.ReadAll(resp.Body)
		log.Printf("Enrollment confirmation failed. Status: %d, Body: %s", resp.StatusCode, string(bodyBytes))
	}
}

// POST /webhooks/mtn/collections
func (h *PaymentHandler) MTNWebhook(c *gin.Context) {
	var payload models.WebhookPayload

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "received", "wali_role": "technology_provider"})
}

// POST /webhooks/wave/payments
func (h *PaymentHandler) WaveWebhook(c *gin.Context) {
	var payload models.WebhookPayload

	_ = c.GetHeader("X-Wave-Signature")

	if err := c.ShouldBindJSON(&payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "received", "wali_role": "technology_provider"})
}
