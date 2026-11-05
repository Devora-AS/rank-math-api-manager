# 📋 Cursor Rules Overview - Rank Math API Manager

## 🎯 **Active Rule Configuration**

### **Primary Rule File (ALWAYS APPLIED)**

- **File**: `comprehensive-development-rules.mdc`
- **Status**: ✅ **ACTIVE** (alwaysApply: true)
- **Scope**: All file types (PHP, JS, CSS, MD, YML, JSON)
- **Purpose**: Contains all current development standards, security requirements, and project-specific rules

### **Reference Files (INACTIVE)**

- **Files**: `development-rules.mdc`, `security-rules.mdc`, `coding-standards.mdc`, `performance-rules.mdc`
- **Status**: 📚 **REFERENCE ONLY** (alwaysApply: false)
- **Purpose**: Quick reference and legacy documentation

## 🚀 **Key Features of Enhanced Rules**

### **1. Project-Specific Context**

- ✅ Plugin name, version, and repository information
- ✅ Current feature status (auto-update system, API endpoints, etc.)
- ✅ WordPress and PHP compatibility requirements

### **2. Mandatory Git Operations Policy**

- ✅ **NEVER commit without explicit user consent**
- ✅ Always ask permission before git operations
- ✅ Provide clear change summaries
- ✅ Use conventional commit messages

### **3. Comprehensive Security Requirements**

- ✅ Input validation and sanitization (mandatory)
- ✅ Output escaping for all data
- ✅ WordPress capability checks
- ✅ Nonce verification for forms/AJAX
- ✅ Security checklist for commits and releases

### **4. WordPress Plugin Standards**

- ✅ Required file structure
- ✅ Plugin header standards
- ✅ Singleton class pattern
- ✅ WordPress API usage requirements
- ✅ Asset enqueuing standards

### **5. Auto-Update System Specific Rules**

- ✅ GitHub API integration requirements
- ✅ Rate limiting implementation (5-minute intervals)
- ✅ Caching requirements (1-hour transients)
- ✅ Authentication token management
- ✅ Release process automation

### **6. Code Quality Standards**

- ✅ WordPress naming conventions
- ✅ Documentation requirements (PHPDoc)
- ✅ Error handling patterns
- ✅ Performance requirements
- ✅ Database operation standards

### **7. Release Process Rules**

- ✅ Version management (multiple locations)
- ✅ GitHub release requirements
- ✅ Automated ZIP creation rules
- ✅ Production file filtering
- ✅ Testing requirements

### **8. Emergency Procedures**

- ✅ Security incident response
- ✅ Auto-update failure procedures
- ✅ Contact information and escalation

## 📋 **Pre-Commit Security Checklist**

Before every commit, the rules require verification of:

- [ ] All user input validated and sanitized
- [ ] All output properly escaped
- [ ] Capability checks implemented
- [ ] Nonce verification for forms/AJAX
- [ ] No sensitive data in logs
- [ ] Error messages don't expose system info
- [ ] SQL queries use prepared statements

## 📦 **Pre-Release Checklist**

Before every release, the rules require:

- [ ] Security audit completed
- [ ] All dependencies updated
- [ ] WordPress compatibility tested
- [ ] Plugin check (PCP) validation passed
- [ ] Auto-update system tested
- [ ] GitHub API rate limiting verified

## 🔧 **Common Development Patterns**

### **REST API Registration**

```php
register_rest_route('rank-math-api/v1', '/update-meta', array(
    'methods'             => 'POST',
    'callback'            => array($this, 'update_meta_callback'),
    'permission_callback' => array($this, 'check_permissions'),
    'args'                => array(
        'post_id' => array(
            'required'          => true,
            'validate_callback' => array($this, 'validate_post_id'),
            'sanitize_callback' => 'intval',
        ),
    ),
));
```

### **GitHub API Integration**

```php
// Rate limiting and authentication
$last_check = get_option('rank_math_api_last_github_check', 0);
if (time() - $last_check < 300) {
    return new WP_Error('rate_limited', 'Rate limited: too many requests');
}

$headers = array(
    'Accept'     => 'application/vnd.github.v3+json',
    'User-Agent' => 'WordPress/' . get_bloginfo('version') . '; ' . get_bloginfo('url')
);

if ($this->github_token) {
    $headers['Authorization'] = 'token ' . $this->github_token;
}
```

### **Security Implementation**

```php
// Input validation
$post_id = intval($_POST['post_id']);
if (!$post_id || $post_id <= 0) {
    return new WP_Error('invalid_post_id', 'Invalid post ID');
}

// Capability check
if (!current_user_can('edit_posts')) {
    return new WP_Error('insufficient_permissions', 'User cannot edit posts');
}

// Output escaping
echo esc_html($user_data);
echo '<input value="' . esc_attr($value) . '">';
```

## 🎯 **Project-Specific Constants**

The rules enforce these required constants:

```php
define('RANK_MATH_API_VERSION', '1.0.8');
define('RANK_MATH_API_PLUGIN_FILE', __FILE__);
define('RANK_MATH_API_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('RANK_MATH_API_PLUGIN_URL', plugin_dir_url(__FILE__));
```

## 📞 **Support and Resources**

### **Documentation**

- [WordPress Developer Handbook](https://developer.wordpress.org/)
- [WordPress Security Best Practices](https://developer.wordpress.org/advanced-administration/security/)
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)

### **Tools**

- [WordPress Plugin Check](https://github.com/WordPress/plugin-check)
- [WordPress Coding Standards](https://github.com/WordPress/WordPress-Coding-Standards)

### **Contact**

- **Security Issues**: security@devora.no
- **Technical Issues**: GitHub Issues
- **Emergency**: Mark as "URGENT" in subject line

## 🔄 **Rule Maintenance**

These rules should be updated when:

- WordPress releases new versions
- Security best practices evolve
- Project requirements change
- New features are implemented
- Performance optimization techniques improve

---

**The enhanced Cursor rules now provide comprehensive guidance for developing the Rank Math API Manager plugin with a focus on security, quality, and maintainability while ensuring consistency with WordPress best practices and project-specific requirements.**
