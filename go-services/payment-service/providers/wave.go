package providers

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
	
	"wali-payment-service/config"
	"wali-payment-service/models"
)

type WaveProvider struct {
	config *config.Config
	client *http.Client
}

func NewWaveProvider(cfg *config.Config) *WaveProvider {
	return &WaveProvider{
		config: cfg,
		client: &http.Client{Timeout: 30 * time.Second},
	}
}

// Create Checkout Session
func (w *WaveProvider) RequestPayment(txn *models.Transaction, phone string) error {
	url := w.config.WaveCheckoutURL
	
	payload := map[string]interface{}{
		"amount":      txn.Amount,
		"currency":    "XOF",
		"client_reference": txn.TransactionRef,
		"payment_method": "mobile_money",
		"customer": map[string]string{
			"phone": phone,
		},
		"success_url": "https://wali.ci/payment/success",
		"cancel_url":  "https://wali.ci/payment/cancel",
		"webhook_url": "https://api.wali.ci/webhooks/wave/payments",
	}
	
	jsonData, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	
	req.Header.Set("Authorization", "Bearer "+w.config.WaveAPIKey)
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := w.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	
	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return fmt.Errorf("wave checkout session failed: %s", string(body))
	}
	
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return err
	}
	
	txn.ProviderResponse = result
	txn.Status = models.StatusPending
	
	// Store checkout URL in provider response
	if checkoutURL, ok := result["checkout_url"].(string); ok {
		txn.ProviderResponse["checkout_url"] = checkoutURL
	}
	
	return nil
}

// Verify Payment Status
func (w *WaveProvider) VerifyPayment(sessionID string) (models.TransactionStatus, error) {
	url := fmt.Sprintf("%s/%s", w.config.WaveCheckoutURL, sessionID)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return models.StatusFailed, err
	}
	
	req.Header.Set("Authorization", "Bearer "+w.config.WaveAPIKey)
	
	resp, err := w.client.Do(req)
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
		case "complete", "paid":
			return models.StatusSuccess, nil
		case "pending", "processing":
			return models.StatusPending, nil
		case "failed", "cancelled":
			return models.StatusFailed, nil
		default:
			return models.StatusPending, nil
		}
	}
	
	return models.StatusPending, nil
}

// Verify Webhook Signature (HMAC-SHA256)
func (w *WaveProvider) VerifyWebhook(signature string, payload []byte) bool {
	mac := hmac.New(sha256.New, []byte(w.config.WaveSecretKey))
	mac.Write(payload)
	expectedSignature := hex.EncodeToString(mac.Sum(nil))
	
	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// Process QR Code Payment (for pharmacy in-person verification)
func (w *WaveProvider) CreateQRCode(txn *models.Transaction) (string, error) {
	// Wave QR code generation endpoint
	url := "https://api.wave.com/v1/qr-codes"
	
	payload := map[string]interface{}{
		"amount":    txn.Amount,
		"currency":  "XOF",
		"reference": txn.TransactionRef,
		"description": fmt.Sprintf("Wali Policy: %s", txn.PolicyID),
	}
	
	jsonData, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", err
	}
	
	req.Header.Set("Authorization", "Bearer "+w.config.WaveAPIKey)
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := w.client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	
	if qrCode, ok := result["qr_code_url"].(string); ok {
		return qrCode, nil
	}
	
	return "", fmt.Errorf("qr code generation failed")
}
