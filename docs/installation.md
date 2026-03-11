# Installation Guide - Rank Math API Manager Plugin

## 📋 Prerequisites

Before installing the Rank Math API Manager plugin, ensure you have:

- **WordPress 5.0 or newer**
- **PHP 7.4 or newer**
- **Rank Math SEO plugin** (installed and activated)
- **Administrator access** to your WordPress site

## 🚀 Installation Methods

### Method 1: Manual Installation (Recommended)

#### Step 1: Download the Plugin

1. Visit the [GitHub repository](https://github.com/devora-as/rank-math-api-manager)
2. Click the green "Code" button
3. Select "Download ZIP"
4. Keep the downloaded ZIP file intact for the WordPress plugin uploader

#### Step 2: Upload to WordPress

1. **Log in to your WordPress admin panel**
2. **Navigate to Plugins → Add New**
3. **Click "Upload Plugin"** at the top of the page
4. **Choose File** and select the downloaded ZIP file
5. **Click "Install Now"**
6. **Activate the plugin** when prompted

![WordPress Plugin Upload](https://via.placeholder.com/800x400/4CAF50/FFFFFF?text=WordPress+Plugin+Upload+Interface)

### Method 2: FTP Installation

#### Step 1: Prepare the Files

1. Download the plugin from GitHub
2. Extract the ZIP file
3. Upload the `rank-math-api-manager` folder to `/wp-content/plugins/`

#### Step 2: Activate the Plugin

1. Log in to WordPress admin
2. Go to **Plugins → Installed Plugins**
3. Find "Rank Math API Manager"
4. Click **"Activate"**

## ⚙️ Configuration

### Step 1: Verify Installation

After activation, you should see:

- ✅ Plugin appears in the plugins list
- ✅ No error messages in WordPress admin
- ✅ REST API endpoints are available

### Step 2: Test API Endpoints

#### Using cURL (Command Line)

```bash
# Test the API endpoint
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [base64-encoded-credentials]" \
  -d "post_id=1&rank_math_title=Test Title"
```

#### Using Postman

1. **Create a new POST request**
2. **URL**: `https://your-site.com/wp-json/rank-math-api/v1/update-meta`
3. **Headers**:
   - `Content-Type: application/x-www-form-urlencoded`
   - `Authorization: Basic [base64-encoded-credentials]`
4. **Body** (form-data):
   - `post_id`: `1`
   - `rank_math_title`: `Test Title`

### Step 3: Set Up Authentication

#### WordPress Application Passwords

1. **Go to Users → Profile**
2. **Scroll to "Application Passwords"**
3. **Enter a name** (e.g., "API Access")
4. **Click "Add New Application Password"**
5. **Copy the generated password**

#### Basic Auth Setup

```bash
# Encode credentials
echo -n "username:password" | base64
```

## 🔧 Integration Setup

### n8n Workflow Integration

1. **Add HTTP Request node** to your n8n workflow
2. **Configure the request**:
   - Method: `POST`
   - URL: `https://your-site.com/wp-json/rank-math-api/v1/update-meta`
   - Headers: Add authentication headers
   - Body: Configure form data

### Example n8n Configuration

```json
{
  "method": "POST",
  "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
  "contentType": "form-urlencoded",
  "headers": {
    "Authorization": "Basic [base64-encoded-credentials]"
  },
  "bodyParameters": {
    "post_id": "={{ $('Post on Wordpress').first().json.id }}",
    "rank_math_title": "={{ $('Generate metatitle e metadescription').first().json.output.metatitle }}",
    "rank_math_description": "={{ $('Generate metatitle e metadescription').first().json.output.metadescription }}",
    "rank_math_focus_keyword": "={{ $('Generate metatitle e metadescription').first().json.output.metakeywords }}"
  }
}
```

## 🛡️ Security Configuration

### 1. Enable HTTPS

Ensure your WordPress site uses HTTPS for secure API communications.

### 2. Restrict API Access

- Use strong application passwords
- Limit API access to trusted applications
- Monitor API usage logs

### 3. WordPress Security

- Keep WordPress updated
- Use security plugins
- Enable two-factor authentication

## 🔍 Verification Steps

### 1. Check Plugin Status

1. Go to **Plugins → Installed Plugins**
2. Verify "Rank Math API Manager" is **Active**
3. Check for any error messages

### 2. Test API Endpoint

```bash
# Test endpoint availability
curl -X GET "https://your-site.com/wp-json/rank-math-api/v1/update-meta"
```

Expected response: `{"code":"rest_no_route","message":"No route was found matching the URL and request method","data":{"status":404}}`

This confirms the endpoint exists but requires POST method.

### 3. Verify Permissions

1. Create a test post
2. Use the API to update its SEO metadata
3. Verify the changes appear in Rank Math

## 🐛 Troubleshooting

### Common Issues

#### Issue: "Plugin could not be activated"

**Solution:**

- Check PHP version (requires 7.4+)
- Verify WordPress version (requires 5.0+)
- Check for plugin conflicts

#### Issue: "401 Unauthorized" API errors

**Solution:**

- Verify application password is correct
- Check that the authenticated user can edit the specific target post or product
- Ensure authentication headers are properly formatted

#### Issue: "404 Not Found" API errors

**Solution:**

- Verify plugin is activated
- Check WordPress REST API is enabled
- Ensure URL is correct

#### Issue: "400 Bad Request" API errors

**Solution:**

- Verify `post_id` exists
- Check parameter formatting
- Ensure all required fields are provided

### Debug Mode

Enable WordPress debug mode for detailed error messages:

```php
// Add to wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

## 📞 Support

If you encounter issues during installation:

1. **Check the troubleshooting section above**
2. **Review WordPress error logs**
3. **Create a GitHub issue** with detailed information
4. **Contact support** at [devora.no](https://devora.no)

### Required Information for Support

- WordPress version
- PHP version
- Plugin version
- Error messages
- Steps to reproduce the issue
- Screenshots (if applicable)

---

**Next Steps**: After installation, see the [API Documentation](api-documentation.md) for detailed usage instructions.

---

**Last Updated**: March 2026  
**Version**: 1.0.9
