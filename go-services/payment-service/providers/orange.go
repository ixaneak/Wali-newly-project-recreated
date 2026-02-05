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

type OrangeMoneyProvider struct {
	config *config.Config
	client *http.Client
	token  string
	tokenExpiry time.Time
}

func NewOrangeMoneyProvider(cfg *config.Config) *OrangeMoneyProvider {
	return &OrangeMoneyProvider{
		config: cfg,
		client: &http.	Client{Timeout: 30 * time.Second},
	}
}

// OAuth2 Token Request
func (o *OrangeMoneyProvider) getAccessToken() error {
	if time.Now().Before(o.tokenExpiry) {
		return nil // Token still valid
	}
	
	url := fmt.Sprintf("%s/oauth/v3/token", o.config.OrangeAPIURL)
	
	data := map[string]string{
		"grant_type": "client_credentials",
	}
	
	jsonData, _ := json.Marshal(data)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	
	req.SetBasicAuth(o.config.OrangeClientID, o.config.OrangeClientSecret)
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := o.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("orange auth failed: %s", string(body))
	}
	
	var tokenResp struct {
		AccessToken string `json:"access_token"`
		ExpiresIn   int    `json:"expires_in"`
	}
	
	if err := json.NewDecoder(resp.Body).Decode(&tokenResp); err != nil {
		return err
	}
	
	o.token = tokenResp.AccessToken
	o.tokenExpiry = time.Now().Add(time.Duration(tokenResp.ExpiresIn) * time.Second)
	
	return nil
}

// Request to Pay
func (o *OrangeMoneyProvider) RequestPayment(txn *models.Transaction, phone string) error {
	if err := o.getAccessToken(); err != nil {
		return fmt.Errorf("failed to get access token: %w", err)
	}
	
	url := fmt.Sprintf("%s/omapi/v1/transactionrequests", o.config.OrangeAPIURL)
	
	payload := map[string]interface{}{
		"transaction": map[string]interface{}{
			"amount":       txn.Amount,
			"currency":     "XOF",
			"reference":    txn.TransactionRef,
			"description":  fmt.Sprintf("Wali Policy Premium - %s", txn.PolicyID),
		},
		"subscriber": map[string]interface{}{
			"msisdn": phone,
		},
		"partner": map[string]interface{}{
			"merchantCode": o.config.OrangeMerchantCode,
		},
	}
	
	jsonData, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	
	req.Header.Set("Authorization", "Bearer "+o.token)
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := o.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	
	body, _ := io.ReadAll(resp.Body)
	
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return fmt.Errorf("orange payment request failed: %s", string(body))
	}
	
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return err
	}
	
	txn.ProviderResponse = result
	
	// Check status
	if status, ok := result["status"].(string); ok {
		switch status {
		case "INITIATED", "PENDING":
			txn.Status = models.StatusPending
		case "SUCCESS":
			txn.Status = models.StatusSuccess
		case "FAILED":
			txn.Status = models.StatusFailed
			if msg, ok := result["message"].(string); ok {
				txn.ErrorMessage = msg
			}
		}
	}
	
	return nil
}

// Verify Payment Status
func (o *OrangeMoneyProvider) VerifyPayment(transactionRef string) (models.TransactionStatus, error) {
	if err := o.getAccessToken(); err != nil {
		return models.StatusFailed, err
	}
	
	url := fmt.Sprintf("%s/omapi/v1/transactionrequests/%s", o.config.OrangeAPIURL, transactionRef)
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return models.StatusFailed, err
	}
	
	req.Header.Set("Authorization", "Bearer "+o.token)
	
	resp, err := o.client.Do(req)
	if err != nil {
		return models.StatusFailed, err
	}
	defer resp.Body.Close()
	
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return models.StatusFailed, err
	}
	
	if status, ok := result["status"].(string); ok {
		switch status {
		case "SUCCESS":
			return models.StatusSuccess, nil
		case "PENDING", "INITIATED":
			return models.StatusPending, nil
		default:
			return models.StatusFailed, nil
		}
	}
	
	return models.StatusPending, nil
}

// Verify Webhook Signature
func (o *OrangeMoneyProvider) VerifyWebhook(signature string, payload []byte) bool {
	// Implement Orange Money webhook signature verification
	// This depends on Orange's specific webhook authentication mechanism
	return true // Placeholder
}
