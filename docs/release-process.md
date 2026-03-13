# Release Process - Rank Math API Manager Plugin

## 📋 Overview

This document outlines the complete process for releasing new versions of the Rank Math API Manager plugin, including automated and manual steps.

## 🔄 Release Types

### **Automated Release Process (Recommended)**

The plugin uses GitHub Actions to automatically create production-ready ZIP files when releases are published.
The workflow also supports a manual recovery path via `workflow_dispatch` for an existing tag/release. This is important if a release was published before a workflow fix was merged, because the original release event may have executed an older workflow definition from the tagged commit.

### **Manual Release Process (Backup)**

Manual process for creating releases when automation is not available.

---

## 🚀 Automated Release Process

### **Step 1: Prepare Release**

1. **Update Version Numbers**

   ```bash
   # Update in rank-math-api-manager.php
   * Version: 1.0.9.1

   # Update in rank-math-api-manager.php constant
   define('RANK_MATH_API_VERSION', '1.0.9.1');
   ```

2. **Update Documentation**

   ```bash
   # Update CHANGELOG.md with new version
   ## [1.0.9.1] - 2026-03-12
   ### Added
   - New features...

   # Update README.md if needed
   # Update any other documentation
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Prepare release v1.0.9.1"
   git push origin main
   ```

### **Step 2: Create GitHub Release**

1. **Go to GitHub Releases**

   - Navigate to: `https://github.com/devora-as/rank-math-api-manager/releases`
   - Click "Create a new release"

2. **Configure Release**

   ```
   Tag version: v1.0.9.1
   Release title: Version 1.0.9.1 - [Brief Description]

   Description:
   ## What's Changed
   - Feature 1: Description
   - Feature 2: Description
   - Bug Fix: Description

   ## Upgrade Notes
   - Any special upgrade instructions

   ## Full Changelog
   See CHANGELOG.md for complete details
   ```

3. **Publish Release**
   - ✅ Set as latest release (checked)
   - ❌ Set as pre-release (unchecked)
   - Click "Publish release"

### **Step 3: Automated ZIP Creation**

The GitHub Action will automatically:

1. **Trigger on Release Publish**

   - Action runs when release is published
   - Uses production-ready file filtering

2. **Create Clean ZIP Structure**

   ```
   rank-math-api-manager.zip
   └── rank-math-api-manager/
       ├── rank-math-api-manager.php
       ├── includes/
       ├── assets/
       ├── README.md
       ├── CHANGELOG.md
       ├── LICENSE.md
       └── readme.txt
   ```

3. **Upload to Release**
   - ZIP file automatically attached as `rank-math-api-manager.zip`
   - Available for WordPress auto-update system

### **Step 3b: Recovery for an Existing Published Release**

If a release already exists but the ZIP asset is missing or the original workflow run failed:

1. Go to **Actions -> Build and Release Plugin**
2. Click **Run workflow**
3. Enter the existing tag (for example `v1.0.9.1`)
4. Run the workflow from `main`

The recovery workflow will:

- resolve the requested tag
- check out the tagged code
- rebuild `rank-math-api-manager.zip`
- upload or overwrite the asset on the existing GitHub release

This avoids rewriting the tag while still ensuring the release gets the exact production ZIP expected by the WordPress updater.

### **Step 4: Verify Release**

1. **Check GitHub Release Page**

   - Verify ZIP asset is attached
   - Confirm the asset name is exactly `rank-math-api-manager.zip`
   - Download and test ZIP structure
   - Confirm the top-level folder is exactly `rank-math-api-manager/`
   - Confirm the main plugin file path is exactly `rank-math-api-manager/rank-math-api-manager.php`

2. **Test Auto-Update System**
   - Check WordPress site with older version
   - Verify update notification appears
   - Test update process

### **Verification: v1.0.8 → v1.0.9.1 update path (fact-based)**

Sites running **v1.0.8** will receive "Update available" for **v1.0.9.1** under the following conditions:

| Fact | Source | Conclusion |
|------|--------|------------|
| v1.0.8 has no download-URL validation | v1.0.8 code sets `package` to `$release_data['download_url']` from the GitHub API with no `is_valid_release_download_url()` (that check was added in 1.0.9). | No code path in 1.0.8 rejects the asset URL. |
| v1.0.8 uses the same GitHub API endpoint | `api.github.com/repos/devora-as/rank-math-api-manager/releases/latest` in both versions. | When v1.0.9.1 is the latest release, the API returns it. |
| Update key is `plugin_basename()` | Both versions use `$plugin_slug = plugin_basename( RANK_MATH_API_PLUGIN_FILE )` and set `$transient->response[ $plugin_slug ]`. | Works for any folder name (e.g. `Rank Math API Manager-plugin-kopi/rank-math-api-manager.php` or `rank-math-api-manager/rank-math-api-manager.php`). |
| Release data is cached 1 hour | v1.0.8 and current code use `get_transient( $cache_key )` with 1-hour TTL. | After publishing v1.0.9.1, sites may need to wait for cache expiry or use "Check Again" / `wp_update_plugins()`. |
| Rate limiting 5 minutes | Both versions throttle GitHub checks to at most one every 5 minutes. | First check after release may be delayed; not a permanent block. |

**Conclusion:** All v1.0.8 sites will see the update **provided** (1) the v1.0.9.1 release is published on GitHub with tag `v1.0.9.1` and asset `rank-math-api-manager.zip`, (2) the site can reach `api.github.com`, and (3) an update check runs after release (scheduled, manual "Check Again", or `wp plugin list` / `wp_update_plugins()`). There is no code path in v1.0.8 that rejects the update.

---

## 🛠️ Manual Release Process

### **When to Use Manual Process**

- GitHub Actions not working
- Custom release requirements
- Emergency releases

### **Manual Steps**

1. **Prepare Files Locally**

   ```bash
   # Navigate to project root
   cd /path/to/plugin/parent/directory

   # Create clean copy
   mkdir temp-release
   cp -r "Rank Math API Manager-plugin" temp-release/rank-math-api-manager

   # Or if your local folder is already named correctly:
   # cp -r rank-math-api-manager temp-release/

   # Remove development files
   cd temp-release/rank-math-api-manager
   rm -rf .git* .github/ tests/ .cursor/ node_modules/
   rm -f .DS_Store TODO*.md .env* .gitignore

   # Verify structure
   ls -la
   ```

2. **Create ZIP File**

   ```bash
   # Return to temp directory
   cd ../

   # Create WordPress-compatible ZIP
   zip -r rank-math-api-manager.zip rank-math-api-manager/

   # Verify ZIP contents
   unzip -l rank-math-api-manager.zip
   ```

3. **Upload to GitHub Release**
   - Create release on GitHub (as in automated process)
   - Manually upload the `rank-math-api-manager.zip` file
   - Ensure filename is exactly `rank-math-api-manager.zip`

---

## 📋 Release Checklist

### **Pre-Release Checklist**

- [ ] Version numbers updated in plugin file
- [ ] CHANGELOG.md updated with new version
- [ ] README.md updated if needed
- [ ] All features tested and working
- [ ] WordPress compatibility verified
- [ ] Security review completed
- [ ] Documentation updated

### **Release Process Checklist**

- [ ] Git branch is clean and up to date
- [ ] Version commit pushed to main branch
- [ ] GitHub release created with correct tag
- [ ] Release description is comprehensive
- [ ] Release published (not draft)
- [ ] ZIP asset automatically attached
- [ ] ZIP file structure verified

### **Post-Release Checklist**

- [ ] Auto-update system tested
- [ ] Download link works
- [ ] ZIP installs correctly in WordPress
- [ ] Version appears correctly after installation
- [ ] All features work in fresh installation
- [ ] Documentation links are working

### **Plugin Check (optional; GitHub-only distribution)**

This plugin is distributed only via GitHub (not WordPress.org). [Plugin Check (PCP)](https://github.com/WordPress/plugin-check) flags custom update logic as errors for directory plugins; for this repo those findings are expected and can be excluded when running checks:

```bash
# From a WordPress site where the plugin and Plugin Check are installed:
wp plugin check rank-math-api-manager --exclude-checks=plugin_updater
```

Optionally ignore the readme "Tested up to" minor-version warning:

```bash
wp plugin check rank-math-api-manager --exclude-checks=plugin_updater --ignore-codes=invalid_tested_upto_minor
```

---

## 🔧 Production File Filter

### **Files Included in Production ZIP**

```
✅ INCLUDED:
- rank-math-api-manager.php (main plugin file)
- includes/ (core functionality)
- assets/ (CSS, JS, images)
- README.md
- LICENSE / LICENSE.md
- CHANGELOG.md
- changelog.txt (WordPress.org format)
- readme.txt (WordPress.org format)

❌ EXCLUDED:
- .git*
- .github/
- tests/
- .cursor/
- node_modules/
- .DS_Store
- TODO*.md
- .env*
- .gitignore
- docs/ (except when specifically needed)
```

### **Automatic File Filtering**

The GitHub Action automatically excludes development files:

```bash
# Remove development directories
rm -rf rank-math-api-manager/.git* 2>/dev/null || true
rm -rf rank-math-api-manager/.github/ 2>/dev/null || true
rm -rf rank-math-api-manager/tests/ 2>/dev/null || true
rm -rf rank-math-api-manager/.cursor/ 2>/dev/null || true
rm -rf rank-math-api-manager/node_modules/ 2>/dev/null || true

# Remove development files
rm -f rank-math-api-manager/.DS_Store 2>/dev/null || true
rm -f rank-math-api-manager/TODO*.md 2>/dev/null || true
rm -f rank-math-api-manager/.env* 2>/dev/null || true
rm -f rank-math-api-manager/.gitignore 2>/dev/null || true
```

---

## 🐛 Troubleshooting

### **Common Issues**

1. **GitHub Action Fails**

   - Check repository permissions
   - Verify GITHUB_TOKEN has correct permissions
   - Check action logs for specific errors
   - If the failed run came from an already-published tag, do not assume re-publishing the same release will use the newest workflow from `main`
   - Use the manual recovery workflow with the release tag to rebuild and upload `rank-math-api-manager.zip`

2. **ZIP Structure Incorrect**

   - Verify folder name **inside** the ZIP is exactly **`rank-math-api-manager`** (lowercase, hyphens). The GitHub Action produces this; manual builds must use the same name.
   - **Important:** The v1.0.8 release ZIP (July 2025) was built with folder **`Rank Math API Manager-plugin-kopi`** inside. Sites that installed from that ZIP have the plugin in that folder. New releases use **`rank-math-api-manager`**. Update notifications still work (plugin uses `plugin_basename()`). For migration to the correct folder name, see **docs/troubleshooting.md** → "Plugin Updates and Folder Name".
   - Check for proper file exclusions
   - Ensure main plugin file is in root of plugin folder

3. **Auto-Update Not Working**
   - Verify ZIP is named exactly `rank-math-api-manager.zip`
   - Check that release is published (not draft)
   - Ensure version number in plugin file matches tag
   - Confirm the GitHub release actually has the ZIP asset attached
   - Remember that WordPress update checks may be delayed by cached transients

### **Emergency Release Process**

If automation fails and urgent release needed:

1. **Create ZIP manually** (follow manual process above)
2. **Upload directly to GitHub release**
3. **Test immediately** on WordPress site
4. **Document issue** for future improvement

---

## 🔐 Security Considerations

### **Release Security**

- ✅ Only trusted maintainers can create releases
- ✅ Automated process prevents human error
- ✅ Production files only (no development secrets)
- ✅ ZIP structure verified before distribution

### **Update Security**

- ✅ WordPress auto-update uses HTTPS
- ✅ File integrity maintained through ZIP structure
- ✅ Version validation prevents downgrade attacks

---

## 📊 Release Metrics

### **Track These Metrics**

1. **Release Frequency**

   - Time between releases
   - Release velocity trends

2. **Update Adoption**

   - How quickly users update
   - Update success rates

3. **Issue Reports**
   - Post-release bug reports
   - Feature requests

---

## 📞 Support

### **Release Issues**

- **Technical Issues**: Create GitHub issue
- **Security Issues**: Email security@devora.no
- **General Questions**: Use GitHub Discussions

### **Emergency Contact**

For critical release issues:

- **Email**: security@devora.no
- **Priority**: Mark as "URGENT - Release Issue"

---

**Last Updated**: March 2026  
**Version**: 1.0.9.1
