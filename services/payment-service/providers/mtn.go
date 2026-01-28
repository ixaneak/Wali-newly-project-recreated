package providers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
	
	"wali-payment-service/config"
	"wali-payment-service/models"
)

type MTNMoMoProvider struct {
	config *config.Config
	client *http.Client
	apiUser string
	apiKey  string
}

func NewMTNMoMoProvider(cfg *config.	Config) *MTNMoMoProvider {
	return &MTNMoMoProvider{
		config:  cfg,
		client:  &http.Client{Timeout: 30 * time.Second},
		apiUser: cfg.MTNAPIUser,
		apiKey:  cfg.MTNAPIKey,
	}
}

// Request to Pay (Collections)
func (m *MTNMoMoProvider) RequestPayment(txn *models.Transaction, phone string) error {
	url := "https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"
	if m.config.MTNTargetEnv == "production" {
		url = "https://proxy.momoapi.mtn.com/collection/v1_0/requesttopay"
	}
	
	// Format phone (remove +225)
	cleanPhone := phone
	if len(phone) > 10 && phone[0] == '+' {
		cleanPhone = phone[4:] // Remove +225
	}
	
	payload := map[string]interface{}{
		"amount":           fmt.Sprintf("%d", txn.Amount),
		"currency":         "XOF",
		"externalId":       txn.TransactionRef,
		"payer": map[string]string{
			"partyIdType": "MSISDN",
			"partyId":     cleanPhone,
		},
		"payerMessage":  "Wali Insurance Premium",
		"payeeNote":     fmt.Sprintf("Policy: %s", txn.PolicyID),
	}
	
	jsonData, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	
	// MTN specific headers
	req.Header.Set("Authorization", "Bearer "+m.apiKey)
	req.Header.Set("X-Reference-Id", txn.TransactionRef)
	req.Header.Set("X-Target-Environment", m.config.MTNTargetEnv)
	req.Header.Set("Ocp-Apim-Subscription-Key", m.config.MTNSubscriptionKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Callback-Url", m.config.MTNCallbackURL)
	
	resp, err := m.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	
	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode != http.StatusAccepted && resp.StatusCode != http.StatusOK {
		return fmt.Errorf("mtn payment request failed [%d]: %s", resp.StatusCode, string(body))
	}
	
	// MTN returns 202 Accepted, need to poll for status
	txn.Status = models.StatusPending
	
	return nil
}

// Verify Payment Status (with polling)
func (m *MTNMoMoProvider) VerifyPayment(transactionRef string) (models.TransactionStatus, error) {
	url := fmt.Sprintf("https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay/%s", transactionRef)
	if m.config.MTNTargetEnv == "production" {
		url = fmt.Sprintf("https://proxy.momoapi.mtn.com/collection/v1_0/requesttopay/%s", transactionRef)
	}
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return models.StatusFailed, err
	}
	
	req.Header.Set("Authorization", "Bearer "+m.apiKey)
	req.Header.Set("X-Target-Environment", m.config.MTNTargetEnv)
	req.Header.Set("Ocp-Apim-Subscription-Key", m.config.MTNSubscriptionKey)
	
	resp, err := m.client.Do(req)
	if err != nil {
		return models.StatusFailed, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return models.StatusFailed, fmt.Errorf("verification failed with status %d", resp.StatusCode)
	}
	
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return models.StatusFailed, err
	}
	
	if status, ok := result["status"].(string); ok {
		switch status {
		case "SUCCESSFUL":
			return models.StatusSuccess, nil
		case "PENDING":
			return models.StatusPending, nil
		case "FAILED":
			return models.StatusFailed, nil
		default:
			return models.StatusPending, nil
		}
	}
	
	return models.StatusPending, nil
}

// Poll for payment status with exponential backoff
func (m *MTNMoMoProvider) PollPaymentStatus(transactionRef string, maxRetries int) (models.TransactionStatus, error) {
	backoff := time.Second
	
	for i := 0; i < maxRetries; i++ {
		status, err := m.VerifyPayment(transactionRef)
		if err != nil {
			return models.StatusFailed, err
		}
		
		if status == models.StatusSuccess || status == models.StatusFailed {
			return status, nil
		}
		
		time.Sleep(backoff)
		backoff *= 2 // Exponential backoff
		if backoff > 30*time.Second {
			backoff = 30 * time.Second
		}
	}
	
	return models.StatusPending, fmt.Errorf("max retries exceeded")
}

// Verify Webhook Signature
func (m *MTNMoMoProvider) VerifyWebhook(signature string, payload []byte) bool {
	// Implement MTN MoMo webhook signature verification
	return true // Placeholder
}
