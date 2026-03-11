# Example Use Cases - Rank Math API Manager Plugin

## 🎯 Overview

This guide provides practical examples of how to use the Rank Math API Manager plugin in various real-world scenarios. Each example includes complete code snippets and step-by-step instructions.

## 📝 Content Syndication

### Scenario: Automatically Update SEO When Content is Syndicated

When content is published on multiple platforms, you need to ensure consistent SEO metadata across all sites.

#### Example: Cross-Site SEO Synchronization

```bash
# Update SEO metadata when content is syndicated
curl -X POST "https://primary-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [base64-encoded-credentials]" \
  -d "post_id=123&rank_math_title=How to Optimize WordPress SEO&rank_math_description=Learn the best practices for optimizing your WordPress site for search engines&rank_math_focus_keyword=WordPress SEO optimization"
```

#### n8n Workflow Example

```json
{
  "nodes": [
    {
      "name": "Content Published",
      "type": "trigger",
      "parameters": {
        "event": "content_published"
      }
    },
    {
      "name": "Generate SEO Metadata",
      "type": "ai_generate",
      "parameters": {
        "prompt": "Generate SEO title, description, and focus keyword for: {{ $('Content Published').first().json.content }}"
      }
    },
    {
      "name": "Update Primary Site",
      "type": "http_request",
      "parameters": {
        "method": "POST",
        "url": "https://primary-site.com/wp-json/rank-math-api/v1/update-meta",
        "headers": {
          "Authorization": "Basic [credentials]"
        },
        "bodyParameters": {
          "post_id": "={{ $('Content Published').first().json.post_id }}",
          "rank_math_title": "={{ $('Generate SEO Metadata').first().json.title }}",
          "rank_math_description": "={{ $('Generate SEO Metadata').first().json.description }}",
          "rank_math_focus_keyword": "={{ $('Generate SEO Metadata').first().json.keyword }}"
        }
      }
    }
  ]
}
```

## 🤖 AI-Driven SEO Optimization

### Scenario: Automatic SEO Generation Based on Content

Use AI to analyze content and generate optimized SEO metadata automatically.

#### Example: AI-Powered SEO Generation

```python
import requests
import json

def generate_seo_metadata(content):
    """Generate SEO metadata using AI"""
    # This would integrate with your AI service
    ai_response = ai_service.analyze(content)

    return {
        'title': ai_response['seo_title'],
        'description': ai_response['seo_description'],
        'keyword': ai_response['focus_keyword']
    }

def update_wordpress_seo(post_id, seo_data):
    """Update WordPress SEO metadata via API"""
    url = "https://your-site.com/wp-json/rank-math-api/v1/update-meta"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic [base64-encoded-credentials]'
    }

    data = {
        'post_id': post_id,
        'rank_math_title': seo_data['title'],
        'rank_math_description': seo_data['description'],
        'rank_math_focus_keyword': seo_data['keyword']
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json()

# Usage example
content = "Your article content here..."
post_id = 123

seo_data = generate_seo_metadata(content)
result = update_wordpress_seo(post_id, seo_data)
print(f"SEO updated: {result}")
```

#### n8n Workflow: AI Content Analysis

```json
{
  "nodes": [
    {
      "name": "New Content",
      "type": "trigger"
    },
    {
      "name": "Analyze Content",
      "type": "openai",
      "parameters": {
        "prompt": "Analyze this content and generate SEO metadata:\n\n{{ $('New Content').first().json.content }}\n\nProvide:\n1. SEO title (max 60 characters)\n2. Meta description (max 160 characters)\n3. Primary focus keyword"
      }
    },
    {
      "name": "Parse AI Response",
      "type": "code",
      "parameters": {
        "code": "const response = $('Analyze Content').first().json.text;\nconst lines = response.split('\\n');\n\nreturn {\n  title: lines[0].replace('1. ', ''),\n  description: lines[1].replace('2. ', ''),\n  keyword: lines[2].replace('3. ', '')\n};"
      }
    },
    {
      "name": "Update SEO",
      "type": "http_request",
      "parameters": {
        "method": "POST",
        "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
        "bodyParameters": {
          "post_id": "={{ $('New Content').first().json.post_id }}",
          "rank_math_title": "={{ $('Parse AI Response').first().json.title }}",
          "rank_math_description": "={{ $('Parse AI Response').first().json.description }}",
          "rank_math_focus_keyword": "={{ $('Parse AI Response').first().json.keyword }}"
        }
      }
    }
  ]
}
```

## 🛒 E-commerce SEO Automation

### Scenario: Product Catalog Optimization

Automatically update SEO metadata for WooCommerce products based on inventory, categories, or seasonal campaigns.

#### Example: Seasonal Product SEO Updates

```bash
# Update product SEO for seasonal campaign
curl -X POST "https://ecommerce-site.com/wp-json/rank-math-api/v1/update-meta" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic [base64-encoded-credentials]" \
  -d "post_id=456&rank_math_title=Christmas Sale - Premium Wireless Headphones&rank_math_description=Get 30% off premium wireless headphones this Christmas. Free shipping and 2-year warranty included.&rank_math_focus_keyword=wireless headphones christmas sale"
```

#### PHP Script: Bulk Product SEO Update

```php
<?php
// Bulk update product SEO metadata
function update_product_seo_bulk($products) {
    $api_url = 'https://your-site.com/wp-json/rank-math-api/v1/update-meta';
    $credentials = base64_encode('username:application_password');

    foreach ($products as $product) {
        $data = [
            'post_id' => $product['id'],
            'rank_math_title' => $product['seo_title'],
            'rank_math_description' => $product['seo_description'],
            'rank_math_focus_keyword' => $product['focus_keyword']
        ];

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $api_url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/x-www-form-urlencoded',
            'Authorization: Basic ' . $credentials
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        $response = curl_exec($ch);
        curl_close($ch);

        echo "Updated product {$product['id']}: " . $response . "\n";
    }
}

// Example usage
$products = [
    [
        'id' => 123,
        'seo_title' => 'Premium Wireless Headphones - Best Sound Quality',
        'seo_description' => 'Experience crystal clear sound with our premium wireless headphones. Perfect for music lovers and professionals.',
        'focus_keyword' => 'premium wireless headphones'
    ],
    [
        'id' => 124,
        'seo_title' => 'Bluetooth Speaker - Portable and Waterproof',
        'seo_description' => 'Take your music anywhere with our portable and waterproof Bluetooth speaker. Perfect for outdoor adventures.',
        'focus_keyword' => 'portable bluetooth speaker'
    ]
];

update_product_seo_bulk($products);
?>
```

## 📊 Bulk SEO Administration

### Scenario: Mass SEO Updates for Multiple Posts

Update SEO metadata for multiple posts at once, useful for site-wide SEO improvements.

#### Example: Category-Based SEO Updates

```javascript
// JavaScript/Node.js example for bulk updates
const axios = require("axios");

async function updateCategorySEO(categoryId, seoTemplate) {
  // First, get all posts in the category
  const postsResponse = await axios.get(
    `https://your-site.com/wp-json/wp/v2/posts?categories=${categoryId}`
  );

  const posts = postsResponse.data;
  const results = [];

  for (const post of posts) {
    try {
      // Generate SEO data based on template and post content
      const seoData = generateSEOFromTemplate(seoTemplate, post);

      // Update via API
      const response = await axios.post(
        "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
        {
          post_id: post.id,
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

      results.push({
        post_id: post.id,
        status: "success",
        response: response.data,
      });
    } catch (error) {
      results.push({
        post_id: post.id,
        status: "error",
        error: error.message,
      });
    }
  }

  return results;
}

function generateSEOFromTemplate(template, post) {
  return {
    title: template.title.replace("{post_title}", post.title.rendered),
    description: template.description.replace(
      "{post_excerpt}",
      post.excerpt.rendered
    ),
    keyword: template.keyword,
  };
}

// Usage
const seoTemplate = {
  title: "{post_title} - Your Brand Name",
  description: "{post_excerpt} Read more about this topic on our website.",
  keyword: "your category keyword",
};

updateCategorySEO(5, seoTemplate)
  .then((results) => console.log("Bulk update results:", results))
  .catch((error) => console.error("Error:", error));
```

## 🔄 Automated Content Workflows

### Scenario: Content Publishing Pipeline

Integrate SEO updates into your content publishing workflow.

#### Example: WordPress + n8n + AI Workflow

```json
{
  "workflow": {
    "name": "Content Publishing with SEO",
    "nodes": [
      {
        "name": "New Post Created",
        "type": "webhook",
        "parameters": {
          "httpMethod": "POST",
          "path": "new-post"
        }
      },
      {
        "name": "Extract Content",
        "type": "code",
        "parameters": {
          "code": "const post = $('New Post Created').first().json;\nreturn {\n  post_id: post.ID,\n  title: post.post_title,\n  content: post.post_content,\n  excerpt: post.post_excerpt\n};"
        }
      },
      {
        "name": "Generate SEO",
        "type": "openai",
        "parameters": {
          "prompt": "Generate SEO metadata for this WordPress post:\n\nTitle: {{ $('Extract Content').first().json.title }}\nContent: {{ $('Extract Content').first().json.content }}\n\nProvide:\n- SEO title (max 60 chars)\n- Meta description (max 160 chars)\n- Primary keyword"
        }
      },
      {
        "name": "Update SEO Metadata",
        "type": "http_request",
        "parameters": {
          "method": "POST",
          "url": "https://your-site.com/wp-json/rank-math-api/v1/update-meta",
          "headers": {
            "Authorization": "Basic [credentials]"
          },
          "bodyParameters": {
            "post_id": "={{ $('Extract Content').first().json.post_id }}",
            "rank_math_title": "={{ $('Generate SEO').first().json.title }}",
            "rank_math_description": "={{ $('Generate SEO').first().json.description }}",
            "rank_math_focus_keyword": "={{ $('Generate SEO').first().json.keyword }}"
          }
        }
      },
      {
        "name": "Send Notification",
        "type": "email",
        "parameters": {
          "to": "admin@your-site.com",
          "subject": "SEO Updated for Post {{ $('Extract Content').first().json.post_id }}",
          "text": "SEO metadata has been automatically updated for the new post."
        }
      }
    ]
  }
}
```

## 📈 Competitor Analysis Integration

### Scenario: SEO Optimization Based on Competitor Analysis

Use competitor analysis tools to generate optimized SEO metadata.

#### Example: Competitor-Based SEO Generation

```python
import requests
import json

def analyze_competitors(keyword):
    """Analyze competitor content for a keyword"""
    # This would integrate with your competitor analysis tool
    competitor_data = competitor_tool.analyze(keyword)

    return {
        'avg_title_length': competitor_data['avg_title_length'],
        'common_keywords': competitor_data['common_keywords'],
        'title_patterns': competitor_data['title_patterns']
    }

def generate_optimized_seo(content, keyword, competitor_data):
    """Generate SEO based on competitor analysis"""
    # Use competitor insights to optimize SEO
    optimized_title = create_title_with_patterns(content, competitor_data['title_patterns'])
    optimized_description = create_description_with_keywords(content, competitor_data['common_keywords'])

    return {
        'title': optimized_title,
        'description': optimized_description,
        'keyword': keyword
    }

def update_wordpress_seo(post_id, seo_data):
    """Update WordPress SEO via API"""
    url = "https://your-site.com/wp-json/rank-math-api/v1/update-meta"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic [base64-encoded-credentials]'
    }

    data = {
        'post_id': post_id,
        'rank_math_title': seo_data['title'],
        'rank_math_description': seo_data['description'],
        'rank_math_focus_keyword': seo_data['keyword']
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json()

# Usage
keyword = "WordPress SEO optimization"
content = "Your article content..."
post_id = 123

competitor_data = analyze_competitors(keyword)
seo_data = generate_optimized_seo(content, keyword, competitor_data)
result = update_wordpress_seo(post_id, seo_data)
```

## 🎯 Best Practices

### 1. Error Handling

Always implement proper error handling in your API calls:

```javascript
try {
  const response = await updateSEO(postId, seoData);
  console.log("SEO updated successfully:", response);
} catch (error) {
  console.error("Failed to update SEO:", error.response?.data || error.message);
  // Implement retry logic or fallback
}
```

### 2. Rate Limiting

Respect API rate limits and implement delays between requests:

```javascript
async function bulkUpdateWithRateLimit(posts, delayMs = 1000) {
  for (const post of posts) {
    await updateSEO(post.id, post.seoData);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
}
```

### 3. Validation

Always validate your data before sending to the API:

```javascript
function validateSEOData(seoData) {
  const errors = [];

  if (!seoData.title || seoData.title.length > 60) {
    errors.push("Title must be between 1-60 characters");
  }

  if (!seoData.description || seoData.description.length > 160) {
    errors.push("Description must be between 1-160 characters");
  }

  if (!seoData.keyword) {
    errors.push("Focus keyword is required");
  }

  return errors;
}
```

---

**Next Steps**: See the [API Documentation](api-documentation.md) for complete technical details.

---

**Last Updated**: March 2026  
**Version**: 1.0.9
