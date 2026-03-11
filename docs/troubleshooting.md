# Troubleshooting Guide - Rank Math API Manager Plugin

## 📋 Overview

This guide helps you identify and resolve common issues with the Rank Math API Manager plugin. Follow the troubleshooting steps to diagnose and fix problems quickly.

## 🔍 Quick Diagnostic Checklist

Before diving into specific issues, run through this checklist:

- ✅ **Plugin is activated** in WordPress admin
- ✅ **Rank Math SEO plugin** is installed and active
- ✅ **WordPress REST API** is accessible
- ✅ **Application Password** is correctly configured
- ✅ **User can edit the specific target post or product**
- ✅ **Post ID exists** and is published
- ✅ **HTTPS is enabled** (recommended for security)

## 🚨 Common Error Codes

### 401 Unauthorized

**Error Message**: `"Authentication required."`

#### Possible Causes:

1. **Invalid credentials**
2. **Missing Application Password**
3. **Incorrect username**
4. **User lacks permissions**

#### Solutions:

**Step 1: Verify Application Password**

```bash
# Test with cURL
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [your-base64-credentials]" \
  -d "post_id=123&rank_math_title=Test"
```

**Step 2: Check User Permissions**

1. Go to **Users → All Users**
2. Find your user account
3. Verify the user can edit the specific target post or product
4. Check if user is active

**Step 3: Regenerate Application Password**

1. Go to **Users → Profile**
2. Scroll to "Application Passwords"
3. Delete existing password
4. Create new Application Password
5. Update your integration

**Step 4: Verify Base64 Encoding**

```bash
# Test encoding
echo -n "username:application_password" | base64
```

### 404 Not Found

**Error Message**: `"No route was found matching the URL and request method"`

#### Possible Causes:

1. **Plugin not activated**
2. **WordPress REST API disabled**
3. **Incorrect endpoint URL**
4. **Permalink structure issues**

#### Solutions:

**Step 1: Check Plugin Status**

1. Go to **Plugins → Installed Plugins**
2. Verify "Rank Math API Manager" is **Active**
3. Check for any error messages

**Step 2: Test REST API**

```bash
# Test WordPress REST API
curl -X GET "https://your-site.com/wp-json/wp/v2/posts"
```

**Step 3: Check Permalinks**

1. Go to **Settings → Permalinks**
2. Select any option other than "Plain"
3. Save changes

**Step 4: Verify Endpoint URL**

```bash
# Test endpoint availability
curl -X GET "https://your-site.com/wp-json/rank-math-api/v1/update-meta"
```

Expected response: 404 (confirms endpoint exists but requires POST)

### 400 Bad Request

**Error Message**: `"No metadata was updated"`

#### Possible Causes:

1. **Missing `post_id`**
2. **Invalid post ID**
3. **No SEO fields provided**
4. **Invalid data format**

#### Solutions:

**Step 1: Verify Post ID**

```bash
# Check if post exists
curl -X GET "https://your-site.com/wp-json/wp/v2/posts/123"
```

**Step 2: Check Request Format**

```bash
# Ensure proper form data
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [credentials]" \
  -d "post_id=123&rank_math_title=Test Title"
```

**Step 3: Verify Post Status**

1. Go to **Posts → All Posts**
2. Find the post by ID
3. Ensure status is "Published"

### 500 Internal Server Error

**Error Message**: Various server error messages

#### Possible Causes:

1. **PHP memory limit exceeded**
2. **Plugin conflicts**
3. **Server configuration issues**
4. **Database connection problems**

#### Solutions:

**Step 1: Enable Debug Mode**

```php
// Add to wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

**Step 2: Check Error Logs**

```bash
# Check WordPress debug log
tail -f wp-content/debug.log

# Check server error logs
tail -f /var/log/apache2/error.log
# or
tail -f /var/log/nginx/error.log
```

**Step 3: Increase Memory Limit**

```php
// Add to wp-config.php
define('WP_MEMORY_LIMIT', '256M');
```

**Step 4: Test Plugin Conflicts**

1. Deactivate all plugins except Rank Math SEO and Rank Math API Manager
2. Test the API endpoint
3. Reactivate plugins one by one to identify conflicts

## 🔧 Integration-Specific Issues

### n8n Integration Problems

#### Issue: Authentication Fails in n8n

**Symptoms**: 401 errors in n8n workflow

**Solutions**:

1. **Check Credential Configuration**

   - Verify username and Application Password
   - Ensure no extra spaces or characters
   - Test credentials manually first

2. **Update n8n Node Configuration**

```json
{
  "authentication": "httpBasicAuth",
  "username": "your_username",
  "password": "your_application_password"
}
```

3. **Test with Simple Request**

```json
{
  "method": "POST",
  "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
  "contentType": "form-urlencoded",
  "bodyParameters": {
    "post_id": "123",
    "rank_math_title": "Test Title"
  }
}
```

#### Issue: Data Mapping Errors

**Symptoms**: Missing or incorrect data in API calls

**Solutions**:

1. **Add Data Validation Node**

```javascript
// Add Code node before HTTP Request
const postId = $("Previous Node").first().json.post_id;
const seoTitle = $("Previous Node").first().json.seo_title;

if (!postId || !seoTitle) {
  throw new Error("Missing required data");
}

return {
  post_id: postId,
  rank_math_title: seoTitle,
  rank_math_description: $("Previous Node").first().json.seo_description || "",
  rank_math_focus_keyword: $("Previous Node").first().json.focus_keyword || "",
};
```

2. **Add Error Handling**

```javascript
// Add Code node after HTTP Request
const response = $("HTTP Request").first().json;

if (response.error) {
  throw new Error(`API Error: ${response.error}`);
}

return {
  success: true,
  data: response,
};
```

### Zapier Integration Problems

#### Issue: Code Action Fails

**Symptoms**: JavaScript errors in Zapier

**Solutions**:

1. **Add Error Handling**

```javascript
try {
  const response = await fetch(
    "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Authorization: "Basic " + btoa("username:application_password"),
      },
      body: new URLSearchParams({
        post_id: inputData.post_id,
        rank_math_title: inputData.seo_title,
        rank_math_description: inputData.seo_description,
        rank_math_focus_keyword: inputData.focus_keyword,
      }),
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      `HTTP ${response.status}: ${result.message || "Unknown error"}`
    );
  }

  return { success: true, data: result };
} catch (error) {
  return { success: false, error: error.message };
}
```

2. **Validate Input Data**

```javascript
// Validate required fields
if (!inputData.post_id) {
  throw new Error("Post ID is required");
}

if (!inputData.seo_title) {
  throw new Error("SEO title is required");
}
```

### Python Integration Problems

#### Issue: SSL Certificate Errors

**Symptoms**: SSL verification failures

**Solutions**:

```python
import requests
import urllib3

# Disable SSL warnings (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Make request with SSL verification disabled
response = requests.post(url, headers=headers, data=data, verify=False)
```

#### Issue: Connection Timeouts

**Symptoms**: Request timeouts

**Solutions**:

```python
import requests

# Set timeout
response = requests.post(url, headers=headers, data=data, timeout=30)

# Retry logic
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

response = session.post(url, headers=headers, data=data)
```

## 🛠️ Advanced Troubleshooting

### Debug Mode Setup

**Step 1: Enable WordPress Debug**

```php
// Add to wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
define('WP_DEBUG_DISPLAY', false);
define('SCRIPT_DEBUG', true);
```

**Step 2: Add Plugin Debug Logging**

```php
// Add to your theme's functions.php or a custom plugin
add_action('rest_api_init', function() {
    error_log('REST API initialized');
});

add_action('wp_rest_server_class', function($class) {
    error_log('REST server class: ' . $class);
});
```

**Step 3: Monitor API Requests**

```php
// Add to your theme's functions.php
add_action('rest_api_init', function() {
    add_filter('rest_pre_dispatch', function($result, $server, $request) {
        error_log('API Request: ' . $request->get_route());
        error_log('API Method: ' . $request->get_method());
        error_log('API Params: ' . json_encode($request->get_params()));
        return $result;
    }, 10, 3);
});
```

### Performance Issues

#### Issue: Slow API Responses

**Solutions**:

1. **Optimize Database Queries**

```php
// Add to wp-config.php
define('SAVEQUERIES', true);
```

2. **Check Server Resources**

```bash
# Monitor server resources
htop
free -h
df -h
```

3. **Enable Caching**

```php
// Add caching headers
add_action('rest_api_init', function() {
    add_filter('rest_post_dispatch', function($response, $handler, $request) {
        $response->header('Cache-Control', 'public, max-age=300');
        return $response;
    }, 10, 3);
});
```

### Security Issues

#### Issue: Unauthorized Access Attempts

**Solutions**:

1. **Implement Rate Limiting**

```php
// Add rate limiting
add_action('rest_api_init', function() {
    add_filter('rest_pre_dispatch', function($result, $server, $request) {
        $ip = $_SERVER['REMOTE_ADDR'];
        $key = 'api_rate_limit_' . $ip;
        $count = get_transient($key);

        if ($count && $count > 100) {
            return new WP_Error('rate_limit_exceeded', 'Rate limit exceeded', ['status' => 429]);
        }

        set_transient($key, ($count ? $count + 1 : 1), 3600);
        return $result;
    }, 10, 3);
});
```

2. **Log Security Events**

```php
// Log failed authentication attempts
add_action('rest_authentication_errors', function($result) {
    if ($result !== null) {
        error_log('Failed API authentication attempt from IP: ' . $_SERVER['REMOTE_ADDR']);
    }
    return $result;
});
```

## 📊 Monitoring and Logging

### Set Up Monitoring

**Step 1: Create Health Check Endpoint**

```php
// Add to your plugin
add_action('rest_api_init', function() {
    register_rest_route('rank-math-api/v1', '/health', [
        'methods' => 'GET',
        'callback' => function() {
            return [
                'status' => 'healthy',
                'timestamp' => current_time('mysql'),
                'version' => '1.0.9'
            ];
        },
        'permission_callback' => '__return_true'
    ]);
});
```

**Step 2: Monitor API Usage**

```php
// Track API usage
add_action('rest_api_init', function() {
    add_filter('rest_post_dispatch', function($response, $handler, $request) {
        if (strpos($request->get_route(), 'rank-math-api') !== false) {
            $usage = get_option('rank_math_api_usage', []);
            $date = date('Y-m-d');
            $usage[$date] = ($usage[$date] ?? 0) + 1;
            update_option('rank_math_api_usage', $usage);
        }
        return $response;
    }, 10, 3);
});
```

### Log Analysis

**Step 1: Parse WordPress Debug Log**

```bash
# Find API-related errors
grep "rank-math-api" wp-content/debug.log

# Find authentication errors
grep "authentication" wp-content/debug.log

# Find recent errors
tail -n 100 wp-content/debug.log | grep "ERROR"
```

**Step 2: Monitor Server Logs**

```bash
# Apache error logs
tail -f /var/log/apache2/error.log | grep "your-domain.com"

# Nginx error logs
tail -f /var/log/nginx/error.log | grep "your-domain.com"
```

## 🆘 Getting Help

### Before Contacting Support

1. **Collect Information**:

   - WordPress version
   - Plugin version
   - PHP version
   - Server environment
   - Complete error messages
   - Request/response data

2. **Test with Minimal Setup**:

   - Deactivate other plugins
   - Switch to default theme
   - Test with basic cURL request

3. **Check Known Issues**:
   - Review GitHub issues
   - Check documentation
   - Search community forums

### Contact Information

- **GitHub Issues**: [Create an issue](https://github.com/devora-as/rank-math-api-manager/issues)
- **Email Support**: [devora.no](https://devora.no)
- **Documentation**: [docs/](docs/)

### Required Information for Support

When contacting support, include:

```
WordPress Version: X.X.X
Plugin Version: X.X.X
PHP Version: X.X.X
Server: Apache/Nginx
Error Message: [Complete error message]
Request Data: [API request details]
Response Data: [API response details]
Steps to Reproduce: [Detailed steps]
Environment: [Local/Staging/Production]
```

---

**Related Documentation**:

- [Installation Guide](installation.md)
- [API Documentation](api-documentation.md)
- [Integration Guide](integration-guide.md)

---

**Last Updated**: March 2026  
**Version**: 1.0.9
