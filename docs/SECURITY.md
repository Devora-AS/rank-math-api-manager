# Security Guide - Rank Math API Manager Plugin

## 📋 Overview

This guide covers security best practices, configuration recommendations, and security features for the Rank Math API Manager plugin. Follow these guidelines to ensure your WordPress site and API endpoints remain secure.

## 🛡️ Security Features

### Built-in Security Measures

The Rank Math API Manager plugin implements several security measures:

#### 1. Authentication & Authorization

- **WordPress Application Passwords**: Secure authentication method
- **User Capability Checks**: Validates `edit_post` access for the specific target post or product
- **Permission Validation**: Ensures users can modify content

#### 2. Input Validation & Sanitization

- **Text Field Sanitization**: Uses `wp_filter_nohtml_kses()` for SEO text fields
- **URL Validation**: Uses `esc_url_raw()` for canonical URLs
- **Post ID Validation**: Ensures posts exist before updates
- **Parameter Validation**: Validates all input parameters

#### 3. Data Protection

- **No Sensitive Data Logging**: API credentials are never logged
- **Secure Transmission**: Requires HTTPS for production use
- **WordPress Nonce Validation**: Where applicable

## 🔐 Authentication Best Practices

### WordPress Application Passwords

#### Setting Up Secure Application Passwords

1. **Create Dedicated User Account**

   ```bash
   # Create a dedicated API user with limited permissions
   # Go to Users → Add New
   # Username: api-user
   # Role: Author or Editor with permission to edit the target post/product
   # Email: api@your-domain.com
   ```

2. **Generate Application Password**

   ```bash
   # Go to Users → Profile → Application Passwords
   # Name: "Rank Math API Access"
   # Click "Add New Application Password"
   # Copy the generated password immediately
   ```

3. **Store Credentials Securely**
   ```bash
   # Never store credentials in plain text
   # Use environment variables or secure configuration
   export WORDPRESS_API_USERNAME="api-user"
   export WORDPRESS_API_PASSWORD="your-application-password"
   ```

#### Credential Management

```bash
# Example: Secure credential storage
# .env file (add to .gitignore)
WORDPRESS_API_USERNAME=api-user
WORDPRESS_API_PASSWORD=your-application-password
WORDPRESS_SITE_URL=https://your-site.com

# Load in your application
source .env
```

### API Key Management (Future Feature)

```php
// Future implementation for API key authentication
add_action('rest_api_init', function() {
    register_rest_route('rank-math-api/v1', '/generate-api-key', [
        'methods' => 'POST',
        'callback' => 'generate_api_key',
        'permission_callback' => function() {
            return current_user_can('manage_options');
        }
    ]);
});

function generate_api_key() {
    $api_key = wp_generate_password(64, false);
    $user_id = get_current_user_id();

    update_user_meta($user_id, 'rank_math_api_key', $api_key);

    return [
        'api_key' => $api_key,
        'created_at' => current_time('mysql')
    ];
}
```

## 🔒 Network Security

### HTTPS Configuration

#### Force HTTPS for API Endpoints

```php
// Add to wp-config.php or theme functions.php
add_action('rest_api_init', function() {
    if (!is_ssl() && !is_admin()) {
        add_filter('rest_authentication_errors', function($result) {
            return new WP_Error('https_required', 'HTTPS is required for API access', ['status' => 403]);
        });
    }
});
```

#### SSL Certificate Validation

```bash
# Test SSL configuration
curl -I https://your-site.com/wp-json/rank-math-api/v1/update-meta

# Check SSL certificate
openssl s_client -connect your-site.com:443 -servername your-site.com
```

### CORS Configuration

#### Default WordPress CORS

The plugin uses WordPress's default CORS settings. For enhanced security:

```php
// Custom CORS configuration
add_action('rest_api_init', function() {
    add_filter('rest_pre_serve_request', function($served, $result, $request, $server) {
        // Allow only specific origins
        $allowed_origins = [
            'https://your-frontend-app.com',
            'https://your-n8n-instance.com'
        ];

        $origin = $_SERVER['HTTP_ORIGIN'] ?? '';

        if (in_array($origin, $allowed_origins)) {
            header('Access-Control-Allow-Origin: ' . $origin);
            header('Access-Control-Allow-Methods: POST, OPTIONS');
            header('Access-Control-Allow-Headers: Content-Type, Authorization');
            header('Access-Control-Allow-Credentials: true');
        }

        return $served;
    }, 10, 4);
});
```

## 🚫 Rate Limiting

### Basic Rate Limiting Implementation

```php
// Add rate limiting to API endpoints
add_action('rest_api_init', function() {
    add_filter('rest_pre_dispatch', function($result, $server, $request) {
        if (strpos($request->get_route(), 'rank-math-api') !== false) {
            $ip = $_SERVER['REMOTE_ADDR'];
            $user_id = get_current_user_id();
            $key = "rate_limit_{$user_id}_{$ip}";

            $count = get_transient($key);
            $limit = 100; // requests per hour
            $window = 3600; // 1 hour

            if ($count && $count >= $limit) {
                return new WP_Error(
                    'rate_limit_exceeded',
                    'Rate limit exceeded. Please try again later.',
                    ['status' => 429]
                );
            }

            set_transient($key, ($count ? $count + 1 : 1), $window);
        }

        return $result;
    }, 10, 3);
});
```

### Advanced Rate Limiting

```php
// Advanced rate limiting with different tiers
class RankMathAPIRateLimiter {
    private $limits = [
        'default' => ['requests' => 100, 'window' => 3600],
        'premium' => ['requests' => 1000, 'window' => 3600],
        'admin' => ['requests' => 10000, 'window' => 3600]
    ];

    public function check_rate_limit($user_id, $ip) {
        $user_tier = $this->get_user_tier($user_id);
        $limit = $this->limits[$user_tier];

        $key = "rate_limit_{$user_tier}_{$user_id}_{$ip}";
        $count = get_transient($key);

        if ($count && $count >= $limit['requests']) {
            return false;
        }

        set_transient($key, ($count ? $count + 1 : 1), $limit['window']);
        return true;
    }

    private function get_user_tier($user_id) {
        if (user_can($user_id, 'manage_options')) {
            return 'admin';
        }

        // Check for premium user status
        if (get_user_meta($user_id, 'premium_user', true)) {
            return 'premium';
        }

        return 'default';
    }
}
```

## 🔍 Input Validation & Sanitization

### Enhanced Input Validation

```php
// Enhanced validation for API parameters
add_action('rest_api_init', function() {
    add_filter('rest_pre_dispatch', function($result, $server, $request) {
        if (strpos($request->get_route(), 'rank-math-api') !== false) {
            $params = $request->get_params();

            // Validate post_id
            if (isset($params['post_id'])) {
                if (!is_numeric($params['post_id']) || $params['post_id'] <= 0) {
                    return new WP_Error('invalid_post_id', 'Invalid post ID', ['status' => 400]);
                }

                $post = get_post($params['post_id']);
                if (!$post || !in_array($post->post_type, ['post', 'product'])) {
                    return new WP_Error('post_not_found', 'Post not found or invalid type', ['status' => 404]);
                }
            }

            // Validate SEO title length
            if (isset($params['rank_math_title'])) {
                if (strlen($params['rank_math_title']) > 60) {
                    return new WP_Error('title_too_long', 'SEO title exceeds 60 characters', ['status' => 400]);
                }
            }

            // Validate SEO description length
            if (isset($params['rank_math_description'])) {
                if (strlen($params['rank_math_description']) > 160) {
                    return new WP_Error('description_too_long', 'SEO description exceeds 160 characters', ['status' => 400]);
                }
            }

            // Validate canonical URL
            if (isset($params['rank_math_canonical_url'])) {
                if (!filter_var($params['rank_math_canonical_url'], FILTER_VALIDATE_URL)) {
                    return new WP_Error('invalid_url', 'Invalid canonical URL', ['status' => 400]);
                }
            }
        }

        return $result;
    }, 10, 3);
});
```

### Content Security

```php
// Prevent XSS and injection attacks
function sanitize_seo_data($data) {
    $sanitized = [];

    if (isset($data['rank_math_title'])) {
        $sanitized['rank_math_title'] = sanitize_text_field($data['rank_math_title']);
    }

    if (isset($data['rank_math_description'])) {
        $sanitized['rank_math_description'] = sanitize_textarea_field($data['rank_math_description']);
    }

    if (isset($data['rank_math_canonical_url'])) {
        $sanitized['rank_math_canonical_url'] = esc_url_raw($data['rank_math_canonical_url']);
    }

    if (isset($data['rank_math_focus_keyword'])) {
        $sanitized['rank_math_focus_keyword'] = sanitize_text_field($data['rank_math_focus_keyword']);
    }

    return $sanitized;
}
```

## 📊 Security Monitoring

### API Access Logging

```php
// Log API access for security monitoring
add_action('rest_api_init', function() {
    add_filter('rest_post_dispatch', function($response, $handler, $request) {
        if (strpos($request->get_route(), 'rank-math-api') !== false) {
            $log_entry = [
                'timestamp' => current_time('mysql'),
                'ip' => $_SERVER['REMOTE_ADDR'],
                'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? '',
                'user_id' => get_current_user_id(),
                'route' => $request->get_route(),
                'method' => $request->get_method(),
                'status' => $response->get_status(),
                'params' => array_keys($request->get_params())
            ];

            // Log to WordPress debug log
            error_log('Rank Math API Access: ' . json_encode($log_entry));

            // Store in database for analysis
            $logs = get_option('rank_math_api_logs', []);
            $logs[] = $log_entry;

            // Keep only last 1000 entries
            if (count($logs) > 1000) {
                $logs = array_slice($logs, -1000);
            }

            update_option('rank_math_api_logs', $logs);
        }

        return $response;
    }, 10, 3);
});
```

### Security Event Monitoring

```php
// Monitor for suspicious activity
add_action('rest_api_init', function() {
    add_filter('rest_authentication_errors', function($result) {
        if ($result !== null) {
            // Log failed authentication attempts
            $log_entry = [
                'timestamp' => current_time('mysql'),
                'ip' => $_SERVER['REMOTE_ADDR'],
                'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? '',
                'route' => $_SERVER['REQUEST_URI'] ?? '',
                'error' => 'Authentication failed'
            ];

            error_log('Rank Math API Security Event: ' . json_encode($log_entry));

            // Alert on multiple failed attempts
            $failed_attempts = get_transient('failed_auth_' . $_SERVER['REMOTE_ADDR']);
            if ($failed_attempts && $failed_attempts > 10) {
                // Send alert email
                wp_mail(
                    get_option('admin_email'),
                    'Security Alert: Multiple Failed API Authentication Attempts',
                    'Multiple failed authentication attempts detected from IP: ' . $_SERVER['REMOTE_ADDR']
                );
            }

            set_transient('failed_auth_' . $_SERVER['REMOTE_ADDR'], ($failed_attempts ? $failed_attempts + 1 : 1), 3600);
        }

        return $result;
    });
});
```

## 🔧 Security Configuration

### WordPress Security Settings

#### Essential Security Plugins

```php
// Recommended security plugins
// 1. Wordfence Security
// 2. Sucuri Security
// 3. iThemes Security
// 4. All In One WP Security & Firewall
```

#### wp-config.php Security

```php
// Add to wp-config.php
// Disable file editing
define('DISALLOW_FILE_EDIT', true);

// Increase memory limit
define('WP_MEMORY_LIMIT', '256M');

// Enable debug logging
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);

// Secure database
define('DB_CHARSET', 'utf8mb4');
define('DB_COLLATE', 'utf8mb4_unicode_ci');

// Force SSL for admin
define('FORCE_SSL_ADMIN', true);
```

### Server Security

#### Apache Security Headers

```apache
# Add to .htaccess
<IfModule mod_headers.c>
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
</IfModule>

# Block access to sensitive files
<Files "wp-config.php">
    Order allow,deny
    Deny from all
</Files>

<Files ".htaccess">
    Order allow,deny
    Deny from all
</Files>
```

#### Nginx Security Headers

```nginx
# Add to nginx.conf
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';";

# Block access to sensitive files
location ~ /(wp-config\.php|\.htaccess) {
    deny all;
}
```

## 🚨 Incident Response

### Security Incident Checklist

1. **Immediate Response**

   - Disable API access if compromised
   - Change all Application Passwords
   - Review server logs for intrusion
   - Check for unauthorized changes

2. **Investigation**

   - Analyze access logs
   - Review API usage patterns
   - Check for data breaches
   - Identify attack vectors

3. **Recovery**
   - Restore from clean backup
   - Update all credentials
   - Implement additional security measures
   - Monitor for further attacks

### Security Contact Information

```php
// Add security contact information
add_action('admin_menu', function() {
    add_options_page(
        'Security Settings',
        'Security',
        'manage_options',
        'security-settings',
        function() {
            ?>
            <div class="wrap">
                <h1>Security Settings</h1>
                <h2>Emergency Contacts</h2>
                <p><strong>Security Email:</strong> security@devora.no</p>
                <p><strong>Emergency Phone:</strong> [Your emergency number]</p>
                <h2>Security Checklist</h2>
                <ul>
                    <li>✅ HTTPS enabled</li>
                    <li>✅ Application Passwords configured</li>
                    <li>✅ Rate limiting enabled</li>
                    <li>✅ Input validation active</li>
                    <li>✅ Security monitoring active</li>
                </ul>
            </div>
            <?php
        }
    );
});
```

## 📋 Security Checklist

### Pre-Deployment Checklist

- [ ] **HTTPS enabled** for all API communications
- [ ] **Application Passwords** configured for API access
- [ ] **User permissions** properly set for the specific target post/product
- [ ] **Input validation** and sanitization active
- [ ] **Rate limiting** implemented
- [ ] **Security headers** configured
- [ ] **Error logging** enabled
- [ ] **Backup strategy** in place
- [ ] **Monitoring** and alerting configured
- [ ] **Incident response plan** documented

### Regular Security Audits

- [ ] **Review access logs** monthly
- [ ] **Update Application Passwords** quarterly
- [ ] **Check for plugin updates** weekly
- [ ] **Review user permissions** monthly
- [ ] **Test security measures** quarterly
- [ ] **Update security documentation** as needed

## 📞 Security Support

### Reporting Security Issues

**Important**: Do not report security issues via GitHub Issues. Send them to **security@devora.no** instead.

### Required Information for Security Reports

```
Subject: Security Issue - Rank Math API Manager

Details:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Environment details
- Proof of concept (if applicable)

Contact Information:
- Your name and email
- Preferred contact method
- Disclosure timeline preference
```

---

**Related Documentation**:

- [Installation Guide](installation.md)
- [API Documentation](api-documentation.md)
- [Troubleshooting Guide](troubleshooting.md)

---

**Last Updated**: March 2026
**Version**: 1.0.9
