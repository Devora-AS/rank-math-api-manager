# Documentation - Rank Math API Manager Plugin

## 📚 Documentation Overview

Welcome to the comprehensive documentation for the Rank Math API Manager plugin. This documentation is organized to help you get started quickly and find the information you need.

## 📖 Available Guides

### 🚀 Getting Started

- **[Installation Guide](installation.md)** - Complete installation and setup instructions
- **[API Documentation](api-documentation.md)** - Complete technical API reference
- **[Example Use Cases](example-use-cases.md)** - Practical examples and scenarios

### 🔧 Integration & Development

- **[Integration Guide](integration-guide.md)** - Step-by-step integration with n8n, Zapier, Make, and custom applications
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
- **[Security Guide](security.md)** - Security best practices and configuration

### 📋 Reference

- **[Changelog](../CHANGELOG.md)** - Version history and changes
- **[Security Policy](../SECURITY.md)** - Security policy and vulnerability reporting
- **[Code of Conduct](../CODE_OF_CONDUCT.md)** - Community guidelines

## 🎯 Quick Start

### 1. Installation

1. Follow the [Installation Guide](installation.md) to set up the plugin
2. Configure WordPress Application Passwords
3. Test the API endpoint

### 2. Basic Usage

```bash
# Update SEO metadata for a post
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [your-credentials]" \
  -d "post_id=123&rank_math_title=Your SEO Title&rank_math_description=Your meta description"
```

### 3. Integration

- **n8n**: See [Integration Guide](integration-guide.md#n8n-integration)
- **Zapier**: See [Integration Guide](integration-guide.md#zapier-integration)
- **Python**: See [Integration Guide](integration-guide.md#python-integration)

## 🔍 Finding What You Need

### By Task

| Task                     | Documentation                               |
| ------------------------ | ------------------------------------------- |
| **Install the plugin**   | [Installation Guide](installation.md)       |
| **Understand the API**   | [API Documentation](api-documentation.md)   |
| **See examples**         | [Example Use Cases](example-use-cases.md)   |
| **Integrate with tools** | [Integration Guide](integration-guide.md)   |
| **Fix problems**         | [Troubleshooting Guide](troubleshooting.md) |
| **Secure your setup**    | [Security Guide](security.md)               |

### By Experience Level

#### Beginner

1. [Installation Guide](installation.md) - Start here
2. [Example Use Cases](example-use-cases.md) - See what's possible
3. [API Documentation](api-documentation.md) - Learn the basics

#### Intermediate

1. [Integration Guide](integration-guide.md) - Connect with your tools
2. [Troubleshooting Guide](troubleshooting.md) - Solve common issues
3. [Security Guide](security.md) - Secure your implementation

#### Advanced

1. [API Documentation](api-documentation.md) - Complete reference
2. [Security Guide](security.md) - Advanced security configuration
3. [Integration Guide](integration-guide.md) - Custom integrations

## 🆘 Getting Help

### Documentation Issues

If you find errors or missing information in the documentation:

- [Create a GitHub issue](https://github.com/devora-as/rank-math-api-manager/issues)
- Include the specific documentation page and section

### Plugin Issues

For plugin bugs or problems:

- [Create a GitHub issue](https://github.com/devora-as/rank-math-api-manager/issues)
- Include error messages and steps to reproduce

### Security Issues

For security vulnerabilities:

- **Email**: security@devora.no
- **Do not** create public GitHub issues for security problems

## 📝 Contributing to Documentation

We welcome contributions to improve the documentation:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Submit a pull request**

### Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Follow the existing format and structure
- Test all code examples before submitting

## 🔄 Documentation Updates

This documentation is updated with each plugin release. Check the [Changelog](../CHANGELOG.md) for the latest changes.

### Version Information

- **Current Version**: 1.0.9
- **Last Updated**: March 2026
- **WordPress Compatibility**: 5.0+
- **PHP Compatibility**: 7.4+

## 📞 Support

- **Documentation**: This documentation
- **GitHub Issues**: [Create an issue](https://github.com/devora-as/rank-math-api-manager/issues)
- **Email Support**: [devora.no](https://devora.no)
- **Security**: security@devora.no

---

**Related Links**:

- [Main README](../README.md)
- [Norwegian Documentation](../README-NORWEGIAN.md)
- [GitHub Repository](https://github.com/devora-as/rank-math-api-manager)

---

**Last Updated**: March 2026  
**Version**: 1.0.9
