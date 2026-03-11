# API Documentation - Rank Math API Manager Plugin

## 📋 Overview

The Rank Math API Manager plugin provides REST API endpoints to programmatically update Rank Math SEO metadata for WordPress posts and WooCommerce products. This documentation covers all available endpoints, parameters, authentication methods, and response formats.

**Compatibility**: Requires WordPress 5.0+ and PHP 7.4+. Verified during local runtime testing on WordPress 6.9.3 and Rank Math 1.0.265.

## 🔗 Base URL

```
https://your-wordpress-site.com/wp-json/rank-math-api/v1/
```

## 🔐 Authentication

### WordPress Application Passwords

The plugin uses WordPress Application Passwords for authentication. You must include the credentials in the `Authorization` header.

#### Setting Up Application Passwords

1. **Log in to WordPress admin**
2. **Go to Users → Profile**
3. **Scroll to "Application Passwords"**
4. **Enter a name** (e.g., "API Access")
5. **Click "Add New Application Password"**
6. **Copy the generated password**

#### Authentication Header Format

```http
Authorization: Basic [base64-encoded-credentials]
```

#### Example: Creating Base64 Credentials

```bash
# Encode username:password
echo -n "username:application_password" | base64
```

#### Example: cURL with Authentication

```bash
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic dXNlcm5hbWU6YXBwbGljYXRpb25fcGFzc3dvcmQ=" \
  -d "post_id=123&rank_math_title=Test Title"
```

## 📡 Endpoints

### POST `/update-meta`

Updates Rank Math SEO metadata for a specific post or product.

#### URL

```
POST /wp-json/rank-math-api/v1/update-meta
```

#### Headers

| Header          | Value                                | Required |
| --------------- | ------------------------------------ | -------- |
| `Content-Type`  | `application/x-www-form-urlencoded`  | Yes      |
| `Authorization` | `Basic [base64-encoded-credentials]` | Yes      |

#### Parameters

| Parameter                 | Type    | Required | Description                          | Example                                                                            |
| ------------------------- | ------- | -------- | ------------------------------------ | ---------------------------------------------------------------------------------- |
| `post_id`                 | integer | Yes      | ID of the post or product            | `14`                                                                               |
| `rank_math_title`         | string  | No       | SEO title (max 60 characters)        | `"How to Optimize WordPress SEO"`                                                  |
| `rank_math_description`   | string  | No       | SEO description (max 160 characters) | `"Learn the best practices for optimizing your WordPress site for search engines"` |
| `rank_math_canonical_url` | URL     | No       | Canonical URL                        | `"https://example.com/post-url"`                                                   |
| `rank_math_focus_keyword` | string  | No       | Primary focus keyword                | `"WordPress SEO optimization"`                                                     |

**Supported post types:** Only **posts** (`post`) and **products** (`product`, if WooCommerce is active). The `post_id` must refer to one of these. Page IDs and other post types will return `rest_invalid_param`.

#### Request Examples

##### Quick test (local or production)

Use a real **post** (or product) ID; page IDs are not supported. Replace the URL and credentials with your site and [Application Password](https://wordpress.org/documentation/article/application-passwords/).

```bash
# Local (e.g. Local by Flywheel)
curl -X POST "http://devora-ny.local/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --user "YOUR_USERNAME:YOUR_APPLICATION_PASSWORD" \
  -d "post_id=14&rank_math_title=Test title&rank_math_description=Test description&rank_math_focus_keyword=test keyword"

# Production
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --user "YOUR_USERNAME:YOUR_APPLICATION_PASSWORD" \
  -d "post_id=14&rank_math_title=Test title&rank_math_description=Test description&rank_math_focus_keyword=test keyword"
```

##### cURL (with Base64 Authorization header)

```bash
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [base64-encoded-credentials]" \
  -d "post_id=123&rank_math_title=How to Optimize WordPress SEO&rank_math_description=Learn the best practices for optimizing your WordPress site for search engines&rank_math_focus_keyword=WordPress SEO optimization"
```

##### JavaScript (Node.js)

```javascript
const axios = require("axios");

async function updateSEO(postId, seoData) {
  try {
    const response = await axios.post(
      "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
      {
        post_id: postId,
        rank_math_title: seoData.title,
        rank_math_description: seoData.description,
        rank_math_focus_keyword: seoData.keyword,
      },
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Authorization: "Basic [base64-encoded-credentials]",
        },
      }
    );

    return response.data;
  } catch (error) {
    console.error("Error updating SEO:", error.response?.data || error.message);
    throw error;
  }
}

// Usage
updateSEO(123, {
  title: "How to Optimize WordPress SEO",
  description:
    "Learn the best practices for optimizing your WordPress site for search engines",
  keyword: "WordPress SEO optimization",
});
```

##### PHP

```php
<?php
function updateRankMathSEO($postId, $seoData) {
    $url = 'https://your-site.com/wp-json/rank-math-api/v1/update-meta';
    $credentials = base64_encode('username:application_password');

    $data = [
        'post_id' => $postId,
        'rank_math_title' => $seoData['title'],
        'rank_math_description' => $seoData['description'],
        'rank_math_focus_keyword' => $seoData['keyword']
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/x-www-form-urlencoded',
        'Authorization: Basic ' . $credentials
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode === 200) {
        return json_decode($response, true);
    } else {
        throw new Exception('Failed to update SEO: ' . $response);
    }
}

// Usage
try {
    $result = updateRankMathSEO(123, [
        'title' => 'How to Optimize WordPress SEO',
        'description' => 'Learn the best practices for optimizing your WordPress site for search engines',
        'keyword' => 'WordPress SEO optimization'
    ]);
    echo "SEO updated successfully: " . json_encode($result);
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}
?>
```

##### Python

```python
import requests
import base64

def update_seo(post_id, seo_data):
    url = "https://your-site.com/wp-json/rank-math-api/v1/update-meta"

    # Encode credentials
    credentials = base64.b64encode(b"username:application_password").decode('utf-8')

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {credentials}'
    }

    data = {
        'post_id': post_id,
        'rank_math_title': seo_data['title'],
        'rank_math_description': seo_data['description'],
        'rank_math_focus_keyword': seo_data['keyword']
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to update SEO: {response.text}")

# Usage
try:
    result = update_seo(123, {
        'title': 'How to Optimize WordPress SEO',
        'description': 'Learn the best practices for optimizing your WordPress site for search engines',
        'keyword': 'WordPress SEO optimization'
    })
    print(f"SEO updated successfully: {result}")
except Exception as e:
    print(f"Error: {e}")
```

#### Response Format

##### Success Response (200 OK)

```json
{
  "rank_math_title": "updated",
  "rank_math_description": "updated",
  "rank_math_focus_keyword": "updated"
}
```

If a submitted value already matches the stored value, the response uses `"unchanged"` for that field instead of `"updated"`.

##### Error Responses

###### 400 Bad Request

Invalid `post_id` (e.g. unsupported post type such as a page, or parameter invalid):

```json
{
  "code": "rest_invalid_param",
  "message": "Invalid parameter(s): post_id",
  "data": {
    "status": 400,
    "params": { "post_id": "Invalid parameter." }
  }
}
```

No metadata was updated:

```json
{
  "code": "no_update",
  "message": "No metadata was updated",
  "data": {
    "status": 400
  }
}
```

###### 401 Unauthorized

```json
{
  "code": "rest_forbidden",
  "message": "Authentication required.",
  "data": {
    "status": 401
  }
}
```

## 🔍 Field Reference

### Supported SEO Fields

| Field           | Meta Key                  | Description                         | Max Length     | Example                                                                            |
| --------------- | ------------------------- | ----------------------------------- | -------------- | ---------------------------------------------------------------------------------- |
| SEO Title       | `rank_math_title`         | Meta title for search engines       | 60 characters  | `"How to Optimize WordPress SEO"`                                                  |
| SEO Description | `rank_math_description`   | Meta description for search engines | 160 characters | `"Learn the best practices for optimizing your WordPress site for search engines"` |
| Canonical URL   | `rank_math_canonical_url` | Canonical URL for duplicate content | Unlimited      | `"https://example.com/post-url"`                                                   |
| Focus Keyword   | `rank_math_focus_keyword` | Primary keyword for the article     | Unlimited      | `"WordPress SEO optimization"`                                                     |

### Post Types Support

The plugin automatically supports:

- **Posts** (`post`) - Standard WordPress posts
- **Products** (`product`) - WooCommerce products (if WooCommerce is active)

## 🛡️ Security & Validation

### Input Validation

The plugin validates and sanitizes all input parameters:

- **Text fields**: Sanitized using `wp_filter_nohtml_kses()`
- **URLs**: Validated using `esc_url_raw()`
- **Post IDs**: Validated to ensure the post exists
- **User permissions**: Checked using `current_user_can( 'edit_post', $post_id )`

### Rate Limiting

The plugin does not currently add a dedicated endpoint rate limiter. The route is authenticated and permission-checked, and additional rate limiting can be added at the site or infrastructure layer if needed.

### CORS

The plugin uses WordPress's default CORS settings. For enhanced security, consider implementing custom CORS policies.

## 🐛 Error Handling

### Common Error Codes

| Error Code            | HTTP Status | Description                                       | Solution                                                                 |
| --------------------- | ----------- | ------------------------------------------------- | ------------------------------------------------------------------------ |
| `rest_forbidden`      | 401         | Authentication is missing or invalid               | Check credentials and authentication headers                             |
| `rest_forbidden`      | 403         | Authenticated user cannot edit the target object   | Use a user who can edit the specific post or product                     |
| `rest_invalid_param`  | 400         | Post ID is invalid or resolves to an unsupported object type | Verify the post/product exists and that pages are not being targeted |
| `no_update`           | 400         | No metadata was updated                           | Ensure at least one field is provided                                    |
| `rest_no_route`       | 404         | Endpoint not found                                | Verify the plugin is activated                                           |

### Error Handling Examples

#### JavaScript

```javascript
async function updateSEOWithErrorHandling(postId, seoData) {
  try {
    const response = await axios.post(
      "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
      {
        post_id: postId,
        rank_math_title: seoData.title,
        rank_math_description: seoData.description,
        rank_math_focus_keyword: seoData.keyword,
      },
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Authorization: "Basic [base64-encoded-credentials]",
        },
      }
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    const errorData = error.response?.data || {};

    return {
      success: false,
      error: {
        code: errorData.code || "unknown_error",
        message: errorData.message || error.message,
        status: error.response?.status || 500,
      },
    };
  }
}
```

#### PHP

```php
<?php
function updateSEOWithErrorHandling($postId, $seoData) {
    $url = 'https://your-site.com/wp-json/rank-math-api/v1/update-meta';
    $credentials = base64_encode('username:application_password');

    $data = [
        'post_id' => $postId,
        'rank_math_title' => $seoData['title'],
        'rank_math_description' => $seoData['description'],
        'rank_math_focus_keyword' => $seoData['keyword']
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/x-www-form-urlencoded',
        'Authorization: Basic ' . $credentials
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode === 200) {
        return [
            'success' => true,
            'data' => json_decode($response, true)
        ];
    } else {
        $errorData = json_decode($response, true);
        return [
            'success' => false,
            'error' => [
                'code' => $errorData['code'] ?? 'unknown_error',
                'message' => $errorData['message'] ?? 'Unknown error occurred',
                'status' => $httpCode
            ]
        ];
    }
}
?>
```

## 📊 Testing

### Test Endpoint Availability

```bash
# Test if the endpoint exists (should return 404 for GET method)
curl -X GET "https://your-site.com/wp-json/rank-math-api/v1/update-meta"
```

Expected response:

```json
{
  "code": "rest_no_route",
  "message": "No route was found matching the URL and request method",
  "data": {
    "status": 404
  }
}
```

### Test Authentication

```bash
# Test with invalid credentials
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic invalid_credentials" \
  -d "post_id=123&rank_math_title=Test"
```

Expected response:

```json
{
  "code": "rest_forbidden",
  "message": "Authentication required.",
  "data": {
    "status": 401
  }
}
```

### Test Valid Request

Use a real **post** (or product) ID. Page IDs will return `rest_invalid_param`.

```bash
# Using --user (curl encodes credentials as Basic auth)
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --user "USERNAME:APPLICATION_PASSWORD" \
  -d "post_id=14&rank_math_title=Test Title&rank_math_description=Test description&rank_math_focus_keyword=test"
```

Alternative with explicit Basic header:

```bash
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [base64-encoded-credentials]" \
  -d "post_id=14&rank_math_title=Test Title"
```

Expected response:

```json
{
  "rank_math_title": "updated"
}
```

## 🔧 Integration Examples

### n8n Workflow Integration

```json
{
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
        "contentType": "form-urlencoded",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpBasicAuth",
        "options": {
          "bodyParameters": {
            "parameters": [
              {
                "name": "post_id",
                "value": "={{ $('Previous Node').first().json.post_id }}"
              },
              {
                "name": "rank_math_title",
                "value": "={{ $('Previous Node').first().json.seo_title }}"
              },
              {
                "name": "rank_math_description",
                "value": "={{ $('Previous Node').first().json.seo_description }}"
              },
              {
                "name": "rank_math_focus_keyword",
                "value": "={{ $('Previous Node').first().json.focus_keyword }}"
              }
            ]
          }
        }
      }
    }
  ]
}
```

### Zapier Integration

```javascript
// Zapier Code Action
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
return { result };
```

## 📈 Performance Considerations

### Best Practices

1. **Batch Updates**: For multiple posts, consider implementing batch processing
2. **Rate Limiting**: Implement delays between requests for bulk operations
3. **Error Handling**: Always implement proper error handling and retry logic
4. **Caching**: Consider caching responses for read operations (when implemented)

### Monitoring

Monitor API usage and performance:

- Track response times
- Monitor error rates
- Log failed requests
- Set up alerts for high error rates

## 🔄 Version History

| Version | Changes                                      |
| ------- | -------------------------------------------- |
| 1.0.9   | WordPress 6.9.3 and Rank Math 1.0.265 compatibility verification, REST hardening |
| 1.0.8   | Auto-update system, enhanced validation      |
| 1.0.7   | Dependency checking, Plugin Check compliance |
| 1.0.6   | Basic SEO field support                      |
| 1.0.5   | Added WooCommerce product support            |
| 1.0.0   | Initial release with basic functionality     |

## 📞 Support

For API-related issues:

1. **Check this documentation**
2. **Review error messages carefully**
3. **Test with the provided examples**
4. **Create a GitHub issue** with detailed information
5. **Contact support** at [devora.no](https://devora.no)

### Required Information for Support

- WordPress version
- Plugin version
- PHP version
- Complete error message
- Request/response data
- Steps to reproduce the issue

---

**Related Documentation**:

- [Installation Guide](installation.md)
- [Example Use Cases](example-use-cases.md)
- [Integration Guide](integration-guide.md)

---

**Last Updated**: March 2026  
**Version**: 1.0.9
