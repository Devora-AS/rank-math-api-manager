# GitHub API Rate Limiting - Rank Math API Manager

## 📋 Overview

The Rank Math API Manager plugin checks GitHub for updates. By default, GitHub allows 60 requests per hour for unauthenticated requests. For sites with many users or frequent update checks, you can configure GitHub authentication to increase this limit to 5,000 requests per hour.

## 🔢 Rate Limits

| Authentication            | Requests/Hour | Recommended For          |
| ------------------------- | ------------- | ------------------------ |
| **Unauthenticated**       | 60            | Small sites (< 10 users) |
| **Personal Access Token** | 5,000         | Large sites (10+ users)  |

## 🚦 When You Need Authentication

Consider setting up GitHub authentication if:

- ✅ Your site has **10+ active users**
- ✅ You have **multiple WordPress sites** using the plugin
- ✅ You're getting **rate limit errors** in debug logs
- ✅ Update checks are **failing frequently**
- ✅ You want **faster update detection**

## 🔐 Setup GitHub Authentication

### **Step 1: Create Personal Access Token**

1. **Go to GitHub Settings**

   - Navigate to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"

2. **Configure Token**

   ```
   Token Name: Rank Math API Updates
   Expiration: No expiration (or 1 year)

   Scopes Required:
   ✅ public_repo (to read public repository releases)

   Optional Scopes (NOT needed):
   ❌ repo (full access - not required)
   ❌ admin:repo_hook
   ❌ delete_repo
   ```

3. **Generate and Copy Token**
   - Click "Generate token"
   - **IMPORTANT**: Copy the token immediately (you won't see it again)
   - Example: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### **Step 2: Configure WordPress**

Choose **ONE** of the following methods:

#### **Method A: WordPress Admin (Recommended)**

1. **Add to wp-config.php**

   ```php
   // Add this line to wp-config.php
   define('RANK_MATH_GITHUB_TOKEN', 'ghp_your_token_here');
   ```

2. **Alternative: Database Option**
   ```php
   // Add this to functions.php temporarily, then remove
   update_option('rank_math_api_github_token', 'ghp_your_token_here');
   ```

#### **Method B: Environment Variable**

1. **Add to .env file**

   ```bash
   RANK_MATH_GITHUB_TOKEN=ghp_your_token_here
   ```

2. **Load in wp-config.php**
   ```php
   // Add to wp-config.php
   if (file_exists(__DIR__ . '/.env')) {
       $env = parse_ini_file(__DIR__ . '/.env');
       define('RANK_MATH_GITHUB_TOKEN', $env['RANK_MATH_GITHUB_TOKEN']);
   }
   ```

### **Step 3: Verify Configuration**

1. **Check Debug Logs**

   - Enable WordPress debugging: `define('WP_DEBUG_LOG', true);`
   - Force update check in WordPress admin
   - Check `/wp-content/debug.log` for:

   ```
   Rank Math API Manager: Using authenticated GitHub API request (5000/hour limit)
   ```

2. **Expected vs Unauthenticated**

   ```bash
   # Unauthenticated (old)
   Rank Math API Manager: Using unauthenticated GitHub API request (60/hour limit)

   # Authenticated (new)
   Rank Math API Manager: Using authenticated GitHub API request (5000/hour limit)
   ```

## 🔧 Advanced Configuration

### **Multiple Sites Setup**

If you manage multiple WordPress sites:

```php
// wp-config.php for all sites
define('RANK_MATH_GITHUB_TOKEN', 'ghp_same_token_for_all_sites');
```

**Benefits:**

- ✅ 5,000 requests/hour **shared across all sites**
- ✅ Much higher than 60/hour per site
- ✅ Single token management

### **Server-Level Configuration**

For server administrators:

```bash
# Add to server environment
export RANK_MATH_GITHUB_TOKEN="ghp_your_token_here"

# Or add to PHP-FPM pool config
env[RANK_MATH_GITHUB_TOKEN] = ghp_your_token_here
```

### **Docker Configuration**

```yaml
# docker-compose.yml
environment:
  - RANK_MATH_GITHUB_TOKEN=ghp_your_token_here
```

## 📊 Monitoring Usage

### **Check Rate Limit Status**

Add this to your `functions.php` temporarily to check current rate limit status:

```php
function check_github_rate_limit() {
    $token = defined('RANK_MATH_GITHUB_TOKEN') ? RANK_MATH_GITHUB_TOKEN : null;

    $headers = array('User-Agent' => 'WordPress-Plugin-Check');
    if ($token) {
        $headers['Authorization'] = 'token ' . $token;
    }

    $response = wp_remote_get('https://api.github.com/rate_limit', array(
        'headers' => $headers
    ));

    if (!is_wp_error($response)) {
        $data = json_decode(wp_remote_retrieve_body($response), true);
        error_log('GitHub Rate Limit Status: ' . print_r($data, true));
    }
}

// Run once to check
check_github_rate_limit();
```

### **Expected Response**

```json
{
  "resources": {
    "core": {
      "limit": 5000, // With token: 5000, Without: 60
      "remaining": 4999, // Requests left in current hour
      "reset": 1635789600 // When limit resets
    }
  }
}
```

## 🚨 Troubleshooting

### **Common Issues**

1. **"Invalid GitHub Token" Error**

   ```bash
   # Check token format
   echo $RANK_MATH_GITHUB_TOKEN
   # Should start with 'ghp_' and be 40 characters
   ```

2. **"Still Getting Rate Limited"**

   - Verify token is properly configured
   - Check debug logs for authentication confirmation
   - Ensure token has `public_repo` scope

3. **"Token Not Working"**
   - Token may have expired
   - Check GitHub token settings
   - Regenerate if necessary

### **Debug Commands**

```php
// Check if token is loaded
var_dump(defined('RANK_MATH_GITHUB_TOKEN'));

// Check current configuration
$plugin = Rank_Math_API_Manager_Extended::get_instance();
// Token is private, but check debug logs for authentication status
```

## 🔒 Security Best Practices

### **Token Security**

1. **Use Minimum Required Permissions**

   - Only enable `public_repo` scope
   - Never use `repo` (full access) unless absolutely necessary

2. **Secure Storage**

   ```php
   // ✅ GOOD: Environment variable or wp-config.php
   define('RANK_MATH_GITHUB_TOKEN', 'ghp_token');

   // ❌ BAD: Never commit tokens to version control
   // ❌ BAD: Never store in public files
   ```

3. **Regular Rotation**

   - Rotate tokens annually
   - Use expiration dates when possible
   - Monitor token usage on GitHub

4. **Access Control**
   ```bash
   # Restrict file permissions
   chmod 600 .env
   chmod 644 wp-config.php
   ```

## 📈 Performance Benefits

### **With GitHub Authentication**

- ✅ **5,000 requests/hour** instead of 60
- ✅ **Faster update detection** for users
- ✅ **Reduced rate limit errors**
- ✅ **Better user experience**

### **Impact on Large Sites**

```
Site Size: 100 active users
Update checks: 24/day per user (hourly checks)
Total requests: 2,400/day

Without token: 60/hour = 1,440/day ❌ (rate limited)
With token: 5,000/hour = 120,000/day ✅ (plenty of headroom)
```

## 📞 Support

### **Need Help?**

1. **Check debug logs first**
2. **Verify token configuration**
3. **Test with rate limit check function**

### **Still Having Issues?**

- **GitHub Issues**: https://github.com/devora-as/rank-math-api-manager/issues
- **Email**: security@devora.no (for token security questions)

---

**Last Updated**: March 2026  
**Version**: 1.0.9
