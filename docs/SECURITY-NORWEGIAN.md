# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.6   | :white_check_mark: |
| 1.0.5   | :white_check_mark: |
| 1.0.0   | :white_check_mark: |
| < 1.0.0 | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in the Rank Math API Manager plugin, please follow these steps:

### 1. **DO NOT** create a public GitHub issue

Security vulnerabilities should be reported privately to prevent potential exploitation.

### 2. **DO** report via email

Send your security report to: **security@devora.no**

### 3. Include the following information in your report:

- **Description**: A clear description of the vulnerability
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact of the vulnerability
- **Environment**: WordPress version, plugin version, and other relevant details
- **Proof of concept**: If possible, include a proof of concept (without exploiting it publicly)

### 4. What to expect:

- **Response time**: We aim to respond within 48 hours
- **Assessment**: We will assess the reported vulnerability
- **Updates**: We will keep you informed of our progress
- **Fix timeline**: Critical vulnerabilities will be addressed within 7 days
- **Credit**: We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Best Practices

### For Users:

1. **Keep WordPress updated**: Always use the latest WordPress version
2. **Update plugins**: Keep all plugins, including this one, updated
3. **Use strong authentication**: Implement strong passwords and two-factor authentication
4. **Limit API access**: Only grant API access to trusted applications
5. **Monitor logs**: Regularly check WordPress and server logs for suspicious activity
6. **Use HTTPS**: Always use HTTPS for API communications

### For Developers:

1. **Input validation**: Always validate and sanitize all input data
2. **Authentication**: Implement proper authentication for all API endpoints
3. **Rate limiting**: Consider implementing rate limiting for API endpoints
4. **Logging**: Log security-relevant events
5. **Error handling**: Don't expose sensitive information in error messages

## Security Features

This plugin implements several security measures:

### Authentication & Authorization:

- WordPress Application Password authentication
- Brukerrettighetskontroller for det konkrete innlegget eller produktet (`edit_post`)
- Proper permission validation for all endpoints

### Input Validation:

- All input parameters are sanitized
- URL validation for canonical URLs
- Text field sanitization using WordPress functions
- Post ID validation

### Data Protection:

- No sensitive data is logged
- Secure transmission via HTTPS
- Proper WordPress nonce validation (where applicable)

## Known Security Considerations

### API Rate Limiting:

Plugin-et har forelopig ingen dedikert rate limiting for API-endepunktet. Ruten er autentisert og tillatelseskontrollert, og ekstra rate limiting kan legges til ved behov.

### CORS:

The plugin uses WordPress's default CORS settings. For enhanced security, consider implementing custom CORS policies.

### Logging:

The plugin doesn't log sensitive data, but ensure your WordPress installation has appropriate logging configured.

## Security Updates

We regularly:

- Review and update dependencies
- Conduct security audits
- Monitor WordPress security advisories
- Test against common vulnerabilities
- Update security best practices

## Responsible Disclosure

We follow responsible disclosure practices:

- We will not publicly disclose vulnerabilities until a fix is available
- We will work with security researchers to understand and fix issues
- We will credit security researchers in our advisories
- We will provide reasonable time for users to update before public disclosure

## Contact Information

- **Security Email**: security@devora.no
- **Company**: Devora AS
- **Website**: https://devora.no
- **GitHub**: https://github.com/devora-as/rank-math-api-manager

---

**Last Updated**: March 2026
