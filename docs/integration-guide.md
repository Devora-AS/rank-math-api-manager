# Integration Guide - Rank Math API Manager Plugin

## 📋 Overview

This guide provides step-by-step instructions for integrating the Rank Math API Manager plugin with various automation tools and platforms. Learn how to connect the plugin with n8n, Zapier, Make (Integromat), and custom applications.

## 🔧 Prerequisites

Before starting integration:

- ✅ **Plugin installed and activated** (see [Installation Guide](installation.md))
- ✅ **WordPress Application Password** configured
- ✅ **Test post or product** created for testing
- ✅ **API endpoint tested** and working

## 🚀 n8n Integration

### Step 1: Set Up n8n

1. **Install n8n** (if not already installed)
2. **Create a new workflow**
3. **Add an HTTP Request node**

### Step 2: Configure HTTP Request Node

#### Basic Configuration

1. **Method**: `POST`
2. **URL**: `https://your-site.com/wp-json/rank-math-api/v1/update-meta`
3. **Content Type**: `form-urlencoded`

#### Authentication Setup

1. **Click on "Add Credential"**
2. **Select "HTTP Basic Auth"**
3. **Enter your WordPress username**
4. **Enter your Application Password**
5. **Save the credential**

#### Body Parameters

Configure the following parameters:

| Parameter                 | Value                                                    | Description                |
| ------------------------- | -------------------------------------------------------- | -------------------------- |
| `post_id`                 | `={{ $('Previous Node').first().json.post_id }}`         | Post ID from previous node |
| `rank_math_title`         | `={{ $('Previous Node').first().json.seo_title }}`       | SEO title                  |
| `rank_math_description`   | `={{ $('Previous Node').first().json.seo_description }}` | SEO description            |
| `rank_math_focus_keyword` | `={{ $('Previous Node').first().json.focus_keyword }}`   | Focus keyword              |

### Step 3: Complete n8n Workflow Example

#### AI Content Generation + SEO Update

```json
{
  "workflow": {
    "name": "AI Content + SEO Update",
    "nodes": [
      {
        "name": "Webhook Trigger",
        "type": "n8n-nodes-base.webhook",
        "parameters": {
          "httpMethod": "POST",
          "path": "new-content",
          "responseMode": "responseNode"
        }
      },
      {
        "name": "Generate SEO with AI",
        "type": "n8n-nodes-base.openAi",
        "parameters": {
          "operation": "completion",
          "model": "gpt-3.5-turbo",
          "prompt": "Generate SEO metadata for this content:\n\nTitle: {{ $('Webhook Trigger').first().json.title }}\nContent: {{ $('Webhook Trigger').first().json.content }}\n\nProvide in JSON format:\n{\n  \"seo_title\": \"SEO title (max 60 chars)\",\n  \"seo_description\": \"Meta description (max 160 chars)\",\n  \"focus_keyword\": \"Primary keyword\"\n}",
          "options": {
            "temperature": 0.7,
            "maxTokens": 200
          }
        }
      },
      {
        "name": "Parse AI Response",
        "type": "n8n-nodes-base.code",
        "parameters": {
          "code": "const aiResponse = $('Generate SEO with AI').first().json.text;\nconst seoData = JSON.parse(aiResponse);\n\nreturn {\n  post_id: $('Webhook Trigger').first().json.post_id,\n  seo_title: seoData.seo_title,\n  seo_description: seoData.seo_description,\n  focus_keyword: seoData.focus_keyword\n};"
        }
      },
      {
        "name": "Update WordPress SEO",
        "type": "n8n-nodes-base.httpRequest",
        "parameters": {
          "method": "POST",
          "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
          "contentType": "form-urlencoded",
          "authentication": "httpBasicAuth",
          "options": {
            "bodyParameters": {
              "parameters": [
                {
                  "name": "post_id",
                  "value": "={{ $('Parse AI Response').first().json.post_id }}"
                },
                {
                  "name": "rank_math_title",
                  "value": "={{ $('Parse AI Response').first().json.seo_title }}"
                },
                {
                  "name": "rank_math_description",
                  "value": "={{ $('Parse AI Response').first().json.seo_description }}"
                },
                {
                  "name": "rank_math_focus_keyword",
                  "value": "={{ $('Parse AI Response').first().json.focus_keyword }}"
                }
              ]
            }
          }
        }
      },
      {
        "name": "Send Success Response",
        "type": "n8n-nodes-base.respondToWebhook",
        "parameters": {
          "respondWith": "json",
          "responseBody": "{\n  \"success\": true,\n  \"message\": \"SEO updated successfully\",\n  \"data\": {{ $('Update WordPress SEO').first().json }}\n}"
        }
      }
    ]
  }
}
```

#### WordPress + n8n Integration

```json
{
  "workflow": {
    "name": "WordPress Post + SEO Update",
    "nodes": [
      {
        "name": "WordPress Webhook",
        "type": "n8n-nodes-base.webhook",
        "parameters": {
          "httpMethod": "POST",
          "path": "wordpress-post",
          "responseMode": "responseNode"
        }
      },
      {
        "name": "Extract Post Data",
        "type": "n8n-nodes-base.code",
        "parameters": {
          "code": "const post = $('WordPress Webhook').first().json;\n\nreturn {\n  post_id: post.ID,\n  title: post.post_title,\n  content: post.post_content,\n  excerpt: post.post_excerpt\n};"
        }
      },
      {
        "name": "Generate SEO",
        "type": "n8n-nodes-base.openAi",
        "parameters": {
          "operation": "completion",
          "model": "gpt-3.5-turbo",
          "prompt": "Generate SEO metadata for this WordPress post:\n\nTitle: {{ $('Extract Post Data').first().json.title }}\nContent: {{ $('Extract Post Data').first().json.content }}\n\nProvide:\n1. SEO title (max 60 characters)\n2. Meta description (max 160 characters)\n3. Primary focus keyword",
          "options": {
            "temperature": 0.7,
            "maxTokens": 150
          }
        }
      },
      {
        "name": "Parse SEO Response",
        "type": "n8n-nodes-base.code",
        "parameters": {
          "code": "const response = $('Generate SEO').first().json.text;\nconst lines = response.split('\\n');\n\nreturn {\n  post_id: $('Extract Post Data').first().json.post_id,\n  seo_title: lines[0].replace(/^\\d+\\.\\s*/, ''),\n  seo_description: lines[1].replace(/^\\d+\\.\\s*/, ''),\n  focus_keyword: lines[2].replace(/^\\d+\\.\\s*/, '')\n};"
        }
      },
      {
        "name": "Update SEO",
        "type": "n8n-nodes-base.httpRequest",
        "parameters": {
          "method": "POST",
          "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
          "contentType": "form-urlencoded",
          "authentication": "httpBasicAuth",
          "options": {
            "bodyParameters": {
              "parameters": [
                {
                  "name": "post_id",
                  "value": "={{ $('Parse SEO Response').first().json.post_id }}"
                },
                {
                  "name": "rank_math_title",
                  "value": "={{ $('Parse SEO Response').first().json.seo_title }}"
                },
                {
                  "name": "rank_math_description",
                  "value": "={{ $('Parse SEO Response').first().json.seo_description }}"
                },
                {
                  "name": "rank_math_focus_keyword",
                  "value": "={{ $('Parse SEO Response').first().json.focus_keyword }}"
                }
              ]
            }
          }
        }
      },
      {
        "name": "Send Notification",
        "type": "n8n-nodes-base.emailSend",
        "parameters": {
          "toEmail": "admin@your-site.com",
          "subject": "SEO Updated for Post {{ $('Parse SEO Response').first().json.post_id }}",
          "text": "SEO metadata has been automatically updated for the new post."
        }
      }
    ]
  }
}
```

### Step 4: Testing the n8n Workflow

1. **Activate the workflow**
2. **Send a test webhook** with sample data
3. **Check the execution logs** for any errors
4. **Verify the SEO update** in WordPress admin

## 🔌 Zapier Integration

### Step 1: Create a Zap

1. **Log in to Zapier**
2. **Click "Create Zap"**
3. **Choose a trigger** (e.g., "New Post" in WordPress)

### Step 2: Add Code Action

1. **Add a "Code by Zapier" action**
2. **Select "Run JavaScript"**
3. **Use the following code**:

```javascript
// Zapier Code Action for SEO Update
const postId = inputData.post_id;
const postTitle = inputData.post_title;
const postContent = inputData.post_content;

// Generate SEO data (you can customize this logic)
const seoTitle =
  postTitle.length > 60 ? postTitle.substring(0, 57) + "..." : postTitle;
const seoDescription =
  postContent.length > 160
    ? postContent.substring(0, 157) + "..."
    : postContent;
const focusKeyword = postTitle.split(" ").slice(0, 3).join(" ");

// Make API request
const response = await fetch(
  "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Authorization: "Basic " + btoa("username:application_password"),
    },
    body: new URLSearchParams({
      post_id: postId,
      rank_math_title: seoTitle,
      rank_math_description: seoDescription,
      rank_math_focus_keyword: focusKeyword,
    }),
  }
);

const result = await response.json();

return {
  success: response.ok,
  data: result,
  post_id: postId,
  seo_title: seoTitle,
  seo_description: seoDescription,
  focus_keyword: focusKeyword,
};
```

### Step 3: Test the Zap

1. **Test the trigger** with a sample post
2. **Check the execution** in Zapier
3. **Verify the results** in WordPress

## 🔗 Make (Integromat) Integration

### Step 1: Create a Scenario

1. **Log in to Make**
2. **Create a new scenario**
3. **Add a trigger** (e.g., WordPress webhook)

### Step 2: Add HTTP Module

1. **Add an HTTP module**
2. **Configure the request**:

#### HTTP Configuration

- **URL**: `https://your-site.com/wp-json/rank-math-api/v1/update-meta`
- **Method**: `POST`
- **Headers**:
  - `Content-Type`: `application/x-www-form-urlencoded`
  - `Authorization`: `Basic [base64-encoded-credentials]`

#### Body Configuration

```json
{
  "post_id": "{{1.post_id}}",
  "rank_math_title": "{{1.seo_title}}",
  "rank_math_description": "{{1.seo_description}}",
  "rank_math_focus_keyword": "{{1.focus_keyword}}"
}
```

### Step 3: Complete Make Scenario

```json
{
  "scenario": {
    "name": "WordPress SEO Update",
    "modules": [
      {
        "name": "WordPress Webhook",
        "type": "webhook",
        "config": {
          "url": "https://hook.eu1.make.com/your-webhook-url"
        }
      },
      {
        "name": "Generate SEO",
        "type": "openai",
        "config": {
          "prompt": "Generate SEO metadata for: {{1.post_title}}",
          "model": "gpt-3.5-turbo"
        }
      },
      {
        "name": "Update SEO",
        "type": "http",
        "config": {
          "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
          "method": "POST",
          "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic [credentials]"
          },
          "body": {
            "post_id": "{{1.post_id}}",
            "rank_math_title": "{{2.seo_title}}",
            "rank_math_description": "{{2.seo_description}}",
            "rank_math_focus_keyword": "{{2.focus_keyword}}"
          }
        }
      }
    ]
  }
}
```

## 🐍 Python Integration

### Step 1: Install Required Packages

```bash
pip install requests
```

### Step 2: Create Integration Script

```python
import requests
import base64
import json
from typing import Dict, Optional

class RankMathAPIClient:
    def __init__(self, site_url: str, username: str, application_password: str):
        self.base_url = f"{site_url}/wp-json/rank-math-api/v1"
        self.credentials = base64.b64encode(
            f"{username}:{application_password}".encode()
        ).decode()

    def update_seo(self, post_id: int, seo_data: Dict[str, str]) -> Dict:
        """
        Update SEO metadata for a post

        Args:
            post_id: WordPress post ID
            seo_data: Dictionary containing SEO data

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}/update-meta"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {self.credentials}'
        }

        data = {
            'post_id': post_id,
            'rank_math_title': seo_data.get('title'),
            'rank_math_description': seo_data.get('description'),
            'rank_math_canonical_url': seo_data.get('canonical_url'),
            'rank_math_focus_keyword': seo_data.get('focus_keyword')
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

    def bulk_update_seo(self, updates: list) -> list:
        """
        Update SEO metadata for multiple posts

        Args:
            updates: List of dictionaries with post_id and seo_data

        Returns:
            List of results for each update
        """
        results = []

        for update in updates:
            try:
                result = self.update_seo(update['post_id'], update['seo_data'])
                results.append({
                    'post_id': update['post_id'],
                    'success': True,
                    'data': result
                })
            except Exception as e:
                results.append({
                    'post_id': update['post_id'],
                    'success': False,
                    'error': str(e)
                })

        return results

# Usage example
def main():
    # Initialize client
    client = RankMathAPIClient(
        site_url="https://your-site.com",
        username="your_username",
        application_password="your_application_password"
    )

    # Single update
    try:
        result = client.update_seo(123, {
            'title': 'How to Optimize WordPress SEO',
            'description': 'Learn the best practices for optimizing your WordPress site for search engines',
            'focus_keyword': 'WordPress SEO optimization'
        })
        print(f"SEO updated successfully: {result}")
    except Exception as e:
        print(f"Error updating SEO: {e}")

    # Bulk update
    updates = [
        {
            'post_id': 123,
            'seo_data': {
                'title': 'Post 1 SEO Title',
                'description': 'Post 1 SEO Description',
                'focus_keyword': 'keyword 1'
            }
        },
        {
            'post_id': 124,
            'seo_data': {
                'title': 'Post 2 SEO Title',
                'description': 'Post 2 SEO Description',
                'focus_keyword': 'keyword 2'
            }
        }
    ]

    results = client.bulk_update_seo(updates)
    for result in results:
        if result['success']:
            print(f"Post {result['post_id']}: Updated successfully")
        else:
            print(f"Post {result['post_id']}: Failed - {result['error']}")

if __name__ == "__main__":
    main()
```

## 🔧 Custom WordPress Integration

### Step 1: WordPress Plugin Integration

```php
<?php
/**
 * Custom WordPress plugin integration example
 */

// Add action to update SEO when post is published
add_action('publish_post', 'auto_update_seo_on_publish', 10, 2);

function auto_update_seo_on_publish($post_id, $post) {
    // Skip revisions and autosaves
    if (wp_is_post_revision($post_id) || wp_is_post_autosave($post_id)) {
        return;
    }

    // Generate SEO data based on post content
    $seo_data = generate_seo_from_content($post);

    // Update via API
    $result = update_seo_via_api($post_id, $seo_data);

    // Log the result
    if ($result['success']) {
        error_log("SEO updated successfully for post {$post_id}");
    } else {
        error_log("Failed to update SEO for post {$post_id}: " . $result['error']);
    }
}

function generate_seo_from_content($post) {
    // Simple SEO generation logic
    $title = wp_trim_words($post->post_title, 8, '');
    $description = wp_trim_words(wp_strip_all_tags($post->post_content), 25, '...');
    $keyword = implode(' ', array_slice(explode(' ', $post->post_title), 0, 3));

    return [
        'title' => $title,
        'description' => $description,
        'focus_keyword' => $keyword
    ];
}

function update_seo_via_api($post_id, $seo_data) {
    $url = home_url('/wp-json/rank-math-api/v1/update-meta');

    // Get application password (you should store this securely)
    $app_password = get_option('rank_math_api_app_password');
    $username = get_option('rank_math_api_username');

    if (!$app_password || !$username) {
        return ['success' => false, 'error' => 'API credentials not configured'];
    }

    $credentials = base64_encode("{$username}:{$app_password}");

    $response = wp_remote_post($url, [
        'headers' => [
            'Content-Type' => 'application/x-www-form-urlencoded',
            'Authorization' => "Basic {$credentials}"
        ],
        'body' => [
            'post_id' => $post_id,
            'rank_math_title' => $seo_data['title'],
            'rank_math_description' => $seo_data['description'],
            'rank_math_focus_keyword' => $seo_data['focus_keyword']
        ],
        'timeout' => 30
    ]);

    if (is_wp_error($response)) {
        return ['success' => false, 'error' => $response->get_error_message()];
    }

    $status_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);

    if ($status_code === 200) {
        return ['success' => true, 'data' => json_decode($body, true)];
    } else {
        return ['success' => false, 'error' => "HTTP {$status_code}: {$body}"];
    }
}

// Add admin settings page
add_action('admin_menu', 'add_rank_math_api_settings_page');

function add_rank_math_api_settings_page() {
    add_options_page(
        'Rank Math API Settings',
        'Rank Math API',
        'manage_options',
        'rank-math-api-settings',
        'rank_math_api_settings_page'
    );
}

function rank_math_api_settings_page() {
    if (isset($_POST['submit'])) {
        update_option('rank_math_api_username', sanitize_text_field($_POST['username']));
        update_option('rank_math_api_app_password', sanitize_text_field($_POST['app_password']));
        echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
    }

    $username = get_option('rank_math_api_username');
    $app_password = get_option('rank_math_api_app_password');
    ?>
    <div class="wrap">
        <h1>Rank Math API Settings</h1>
        <form method="post">
            <table class="form-table">
                <tr>
                    <th scope="row">Username</th>
                    <td><input type="text" name="username" value="<?php echo esc_attr($username); ?>" class="regular-text" /></td>
                </tr>
                <tr>
                    <th scope="row">Application Password</th>
                    <td><input type="password" name="app_password" value="<?php echo esc_attr($app_password); ?>" class="regular-text" /></td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}
?>
```

## 🧪 Testing Your Integration

### Step 1: Create Test Data

```bash
# Create a test post
curl -X POST "https://your-site.com/wp-json/wp/v2/posts" \
  -H "Authorization: Basic [credentials]" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Post for SEO Integration",
    "content": "This is a test post to verify the SEO integration is working correctly.",
    "status": "publish"
  }'
```

### Step 2: Test SEO Update

```bash
# Test the SEO update
curl -X POST "https://your-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [credentials]" \
  -d "post_id=123&rank_math_title=Test SEO Title&rank_math_description=Test SEO description for integration testing&rank_math_focus_keyword=test integration"
```

### Step 3: Verify Results

1. **Check WordPress admin** for updated SEO metadata
2. **View the post** to see the changes
3. **Check Rank Math SEO** settings for the post

## 🐛 Troubleshooting

### Common Integration Issues

#### Issue: Authentication Errors

**Symptoms**: 401 Unauthorized errors
**Solutions**:

- Verify Application Password is correct
- Check username spelling
- Ensure credentials are properly encoded

#### Issue: Post Not Found

**Symptoms**: 404 errors
**Solutions**:

- Verify post ID exists
- Check post status (published vs draft)
- Ensure post type is supported

#### Issue: Invalid Data

**Symptoms**: 400 Bad Request errors
**Solutions**:

- Check parameter names and values
- Verify data types
- Ensure required fields are provided

### Debug Mode

Enable WordPress debug mode for detailed error messages:

```php
// Add to wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

### Logging

Add logging to your integration:

```javascript
// JavaScript logging
console.log("API Request:", {
  url: apiUrl,
  data: requestData,
  headers: requestHeaders,
});

console.log("API Response:", response);
```

```php
// PHP logging
error_log('Rank Math API Request: ' . json_encode($request_data));
error_log('Rank Math API Response: ' . json_encode($response));
```

## 📞 Support

For integration issues:

1. **Check this documentation**
2. **Review error messages**
3. **Test with provided examples**
4. **Create a GitHub issue** with details
5. **Contact support** at [devora.no](https://devora.no)

### Required Information for Support

- Integration platform (n8n, Zapier, etc.)
- Complete error messages
- Request/response data
- Steps to reproduce the issue
- WordPress and plugin versions

---

**Related Documentation**:

- [Installation Guide](installation.md)
- [API Documentation](api-documentation.md)
- [Example Use Cases](example-use-cases.md)

---

**Last Updated**: March 2026  
**Version**: 1.0.9
