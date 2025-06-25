# Security Guidelines - Codex Umbra

## API Key Security

### ⚠️ CRITICAL: Never Expose Secrets

**NEVER:**
- Print API keys in logs, console output, or user interfaces
- Include secrets in error messages or debugging output
- Display keys in configuration validation messages
- Store secrets in version control (git)
- Pass secrets as URL parameters or in HTTP headers unnecessarily

**ALWAYS:**
- Check for key existence without revealing values
- Use "configured/not configured" status messages
- Mask or redact secrets in all outputs
- Use environment variables for secret storage
- Validate key format without displaying content

### Implementation Examples

#### ✅ Secure Configuration Validation
```bash
# Good: Check existence without revealing value
if grep -q '^ANTHROPIC_API_KEY=.*[^=]$' .env; then
    echo "✅ ANTHROPIC_API_KEY: configured"
else
    echo "⚠️ ANTHROPIC_API_KEY: not configured"
fi
```

#### ❌ Insecure Validation (NEVER DO THIS)
```bash
# BAD: Exposes secret value
echo "API Key: $(grep '^ANTHROPIC_API_KEY=' .env | cut -d'=' -f2)"
```

#### ✅ Secure Logging
```python
# Good: Log configuration status without values
if settings.anthropic_api_key:
    logger.info("Anthropic provider initialized (key configured)")
else:
    logger.info("Anthropic provider skipped (no API key configured)")
```

#### ❌ Insecure Logging (NEVER DO THIS)
```python
# BAD: Logs actual secret
logger.info(f"Using API key: {settings.anthropic_api_key}")
```

### Environment File Security

#### .env File Handling
- **Always** add `.env` to `.gitignore`
- **Never** commit actual `.env` files
- **Provide** `.env.example` as template
- **Use** placeholder values in examples

#### Example .env.example Format
```bash
# Good: Template with placeholder
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Bad: Real key in template
ANTHROPIC_API_KEY=sk-ant-api03-xyz123...
```

### Runtime Security

#### Error Messages
```python
# Good: Generic error without secret exposure
except Exception as e:
    logger.error("Authentication failed for provider")
    
# Bad: May expose secret in error details
except Exception as e:
    logger.error(f"API call failed: {e}")
```

#### Health Checks
```python
# Good: Boolean result without details
async def is_available(self) -> bool:
    try:
        # Test API without logging request/response
        response = await client.test_auth()
        return response.status == 200
    except:
        return False

# Bad: Exposes request details
async def is_available(self) -> bool:
    try:
        response = await client.test_auth()
        logger.info(f"Auth response: {response}")  # May contain secrets
        return True
    except Exception as e:
        logger.error(f"Auth failed: {e}")  # May expose API key
        return False
```

## Configuration Security

### Provider Initialization
- Check key existence before provider creation
- Log configuration status, not values
- Gracefully handle missing keys
- Validate key format without revealing content

### Response Security
- Never include API keys in response metadata
- Mask provider credentials in debug info
- Use generic identifiers for providers
- Sanitize all user-facing outputs

## Makefile Security

### Environment Validation
```makefile
# Good: Check without display
check-api-key:
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "❌ API key not configured"; \
	else \
		echo "✅ API key configured"; \
	fi

# Bad: Exposes value
check-api-key:
	@echo "API Key: $$ANTHROPIC_API_KEY"
```

### Test Commands
```makefile
# Good: Test without exposing secrets
test-provider:
	@curl -s http://localhost:8000/api/v1/llm/providers | jq '.providers[].available'

# Bad: May log sensitive data
test-provider:
	@curl -v http://localhost:8000/api/v1/chat -d '{"key": "$(ANTHROPIC_API_KEY)"}'
```

## Development Guidelines

### Code Review Checklist
- [ ] No hardcoded secrets in source code
- [ ] No secrets in log statements
- [ ] Environment variables used for configuration
- [ ] Error messages don't expose secrets
- [ ] Test data uses mock/placeholder values
- [ ] Debug output sanitized

### Local Development
- Use separate API keys for development/production
- Never share .env files between developers
- Rotate keys if accidentally exposed
- Use minimal permissions for API keys

### CI/CD Security
- Store secrets in encrypted environment variables
- Never echo secrets in build logs
- Use masked variables in CI systems
- Validate secret format in pipelines

## Incident Response

### If Secret is Exposed
1. **Immediately revoke** the exposed key
2. **Generate new** API key
3. **Update** all environments with new key
4. **Review** logs for unauthorized usage
5. **Document** incident and prevention measures

### Prevention Measures
- Regular security audits of logs and outputs
- Automated scanning for hardcoded secrets
- Developer training on secure coding practices
- Code review focus on secret handling