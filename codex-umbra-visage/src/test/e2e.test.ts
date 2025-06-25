import { describe, it, expect, beforeAll, afterAll } from 'vitest'

const CONDUCTOR_URL = 'http://localhost:8000'
const FRONTEND_URL = 'http://localhost:5173'

describe('Codex Umbra End-to-End Tests', () => {
  beforeAll(async () => {
    // Check if services are running
    try {
      const conductorResponse = await fetch(`${CONDUCTOR_URL}/health`)
      expect(conductorResponse.ok).toBe(true)
    } catch (error) {
      throw new Error('Conductor service is not running. Please start it with: cd conductor_project && uvicorn app.main:app --reload --port 8000')
    }
  })

  describe('API Integration Tests', () => {
    it('should handle basic chat interaction', async () => {
      const response = await fetch(`${CONDUCTOR_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Hello, this is a test message',
          user_id: 'test_user'
        })
      })

      expect(response.ok).toBe(true)
      const data = await response.json()
      expect(data).toHaveProperty('response')
      expect(data).toHaveProperty('timestamp')
      expect(typeof data.response).toBe('string')
      expect(data.response.length).toBeGreaterThan(0)
    })

    it('should handle natural language queries', async () => {
      const testQueries = [
        'What is the weather like today?',
        'Tell me a joke',
        'What is 2 + 2?',
        'Explain quantum computing in simple terms'
      ]

      for (const query of testQueries) {
        const response = await fetch(`${CONDUCTOR_URL}/api/v1/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: query,
            user_id: 'test_user'
          })
        })

        expect(response.ok).toBe(true)
        const data = await response.json()
        expect(data).toHaveProperty('response')
        expect(data.response).toBeTruthy()
        expect(typeof data.response).toBe('string')
        
        // Response should be meaningful (not just an error message)
        expect(data.response).not.toMatch(/error|Error|ERROR/)
        expect(data.response.length).toBeGreaterThan(10)
      }
    })

    it('should handle LLM provider endpoints', async () => {
      // Test getting available providers
      const providersResponse = await fetch(`${CONDUCTOR_URL}/api/v1/llm/providers`)
      expect(providersResponse.ok).toBe(true)
      
      const providers = await providersResponse.json()
      expect(Array.isArray(providers)).toBe(true)
      expect(providers.length).toBeGreaterThan(0)
    })

    it('should handle health checks', async () => {
      // Test Conductor health
      const conductorHealth = await fetch(`${CONDUCTOR_URL}/health`)
      expect(conductorHealth.ok).toBe(true)
      
      const conductorData = await conductorHealth.json()
      expect(conductorData).toHaveProperty('status', 'healthy')

      // Test Sentinel health through Conductor
      const sentinelHealth = await fetch(`${CONDUCTOR_URL}/api/v1/sentinel/health`)
      expect(sentinelHealth.ok).toBe(true)
      
      const sentinelData = await sentinelHealth.json()
      expect(sentinelData).toHaveProperty('status', 'healthy')
    })
  })

  describe('Error Handling Tests', () => {
    it('should handle invalid requests gracefully', async () => {
      const response = await fetch(`${CONDUCTOR_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Missing required fields
        })
      })

      expect(response.status).toBe(422) // Validation error
    })

    it('should handle empty messages', async () => {
      const response = await fetch(`${CONDUCTOR_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: '',
          user_id: 'test_user'
        })
      })

      // Should either accept empty message or return meaningful error
      expect([200, 400, 422]).toContain(response.status)
    })
  })

  describe('Performance Tests', () => {
    it('should respond within reasonable time limits', async () => {
      const startTime = Date.now()
      
      const response = await fetch(`${CONDUCTOR_URL}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Quick test message',
          user_id: 'test_user'
        })
      })

      const endTime = Date.now()
      const responseTime = endTime - startTime

      expect(response.ok).toBe(true)
      expect(responseTime).toBeLessThan(30000) // 30 seconds max
    })
  })
})