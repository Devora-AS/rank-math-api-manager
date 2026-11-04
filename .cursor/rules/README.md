# Development Rules - Rank Math API Manager Plugin

## 📋 Overview

This directory contains comprehensive development rules and guidelines for the Rank Math API Manager plugin. These rules ensure consistent code quality, security, and performance across all development work.

## 🎯 **Primary Rule File**

**[comprehensive-development-rules.mdc](comprehensive-development-rules.mdc)** - This is the main, always-applied rule file containing all current development standards, security requirements, and best practices for the project.

## 📁 File Structure

```
.cursor/rules/
├── README.md                              # This file - Overview and index
├── comprehensive-development-rules.mdc    # 🎯 MAIN RULES (always applied)
├── development-rules.mdc                  # Legacy - for reference only
├── security-rules.mdc                     # Quick reference only
├── coding-standards.mdc                   # Quick reference only
└── performance-rules.mdc                  # Quick reference only
```

## 🎯 Purpose

These rules serve as a comprehensive guide for:

1. **Code Quality**: Ensuring consistent, maintainable, and readable code
2. **Security**: Implementing WordPress security best practices
3. **Performance**: Optimizing for speed and efficiency
4. **Standards**: Following WordPress coding standards and conventions
5. **Best Practices**: Leveraging WordPress Plugin API and development patterns

## 📖 Rule Categories

### 1. [Development Rules](development-rules.md)

- Git operations and version control
- WordPress plugin development best practices
- Code quality standards
- Documentation requirements
- Testing requirements
- Plugin-specific rules

### 2. [Security Rules](security-rules.md)

- Input validation and sanitization
- Output escaping
- Nonce verification
- Capability checks
- API security
- Security testing
- Incident response

### 3. [Coding Standards](coding-standards.md)

- PHP coding standards
- WordPress naming conventions
- File organization
- WordPress Plugin API usage
- Database operations
- Testing standards

### 4. [Performance Rules](performance-rules.md)

- Database optimization
- Caching strategies
- Asset optimization
- API performance
- Performance monitoring
- Memory usage optimization

## 🚀 Getting Started

### For New Developers

1. Read through all rule files to understand the project standards
2. Pay special attention to security rules and WordPress coding standards
3. Use the checklists provided in each file
4. Follow the code examples and patterns provided

### For Code Reviews

1. Use the security checklist before approving any changes
2. Verify WordPress coding standards compliance
3. Check performance implications of changes
4. Ensure proper documentation is included

### For Releases

1. Run through all checklists in the rule files
2. Perform security audit
3. Test performance impact
4. Verify WordPress compatibility

## 🔧 Integration with Development Workflow

### Pre-commit Checklist

- [ ] Code follows WordPress coding standards
- [ ] Security requirements are met
- [ ] Performance considerations addressed
- [ ] Documentation updated
- [ ] Tests pass

### Code Review Checklist

- [ ] Security rules followed
- [ ] WordPress best practices implemented
- [ ] Performance optimized
- [ ] Error handling implemented
- [ ] Input validation and sanitization applied

### Release Checklist

- [ ] All security requirements met
- [ ] Performance tested
- [ ] WordPress compatibility verified
- [ ] Documentation complete
- [ ] Changelog updated

## 🛠️ Tools and Resources

### WordPress Development Tools

- [WordPress Plugin Check (PCP)](https://github.com/WordPress/plugin-check)
- [WordPress Coding Standards for PHP_CodeSniffer](https://github.com/WordPress/WordPress-Coding-Standards)
- [PHPUnit for WordPress](https://make.wordpress.org/core/handbook/testing/automated-testing/phpunit/)

### Security Tools

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [WordPress Security Scanner](https://wordpress.org/plugins/wordfence/)
- [PHP Security Checker](https://security.symfony.com/)

### Performance Tools

- [Query Monitor](https://wordpress.org/plugins/query-monitor/)
- [GTmetrix](https://gtmetrix.com/)
- [New Relic](https://newrelic.com/)

## 📚 Documentation Resources

### WordPress Official Documentation

- [WordPress Developer Handbook](https://developer.wordpress.org/)
- [WordPress Plugin Handbook](https://developer.wordpress.org/plugins/)
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [WordPress Coding Standards](https://developer.wordpress.org/coding-standards/)

### Security Resources

- [WordPress Security Best Practices](https://developer.wordpress.org/advanced-administration/security/)
- [OWASP PHP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Security_Cheat_Sheet.html)
- [WordPress Security Team](https://make.wordpress.org/security/)

### Performance Resources

- [WordPress Performance](https://developer.wordpress.org/advanced-administration/performance/)
- [WordPress Database Optimization](https://developer.wordpress.org/advanced-administration/performance/database/)
- [WordPress Caching](https://developer.wordpress.org/advanced-administration/performance/caching/)

## 🤝 Contributing

When contributing to this project:

1. **Follow all rules** outlined in these files
2. **Ask questions** if any rules are unclear
3. **Suggest improvements** to the rules when appropriate
4. **Update documentation** when adding new features
5. **Test thoroughly** before submitting changes

## 📞 Support

If you have questions about these rules or need clarification:

1. Check the WordPress documentation resources listed above
2. Review the code examples provided in each rule file
3. Consult with the development team
4. Refer to the security and performance checklists

## 🔄 Updates

These rules are living documents that should be updated as:

- WordPress releases new versions
- Security best practices evolve
- Performance optimization techniques improve
- New development tools become available
- Project requirements change

---

**Remember**: These rules are designed to ensure the highest quality, security, and performance for the Rank Math API Manager plugin. Following them consistently will result in better code, fewer bugs, and a more maintainable codebase.
