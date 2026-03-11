# Release Process - Rank Math API Manager Plugin

## 📋 Overview

This document outlines the complete process for releasing new versions of the Rank Math API Manager plugin, including automated and manual steps.

## 🔄 Release Types

### **Automated Release Process (Recommended)**

The plugin uses GitHub Actions to automatically create production-ready ZIP files when releases are published.

### **Manual Release Process (Backup)**

Manual process for creating releases when automation is not available.

---

## 🚀 Automated Release Process

### **Step 1: Prepare Release**

1. **Update Version Numbers**

   ```bash
   # Update in rank-math-api-manager.php
   * Version: 1.0.9

   # Update in rank-math-api-manager.php constant
   define('RANK_MATH_API_VERSION', '1.0.9');
   ```

2. **Update Documentation**

   ```bash
   # Update CHANGELOG.md with new version
   ## [1.0.9] - 2025-08-01
   ### Added
   - New features...

   # Update README.md if needed
   # Update any other documentation
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Prepare release v1.0.9"
   git push origin main
   ```

### **Step 2: Create GitHub Release**

1. **Go to GitHub Releases**

   - Navigate to: `https://github.com/devora-as/rank-math-api-manager/releases`
   - Click "Create a new release"

2. **Configure Release**

   ```
   Tag version: v1.0.9
   Release title: Version 1.0.9 - [Brief Description]

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

### **Step 4: Verify Release**

1. **Check GitHub Release Page**

   - Verify ZIP asset is attached
   - Download and test ZIP structure

2. **Test Auto-Update System**
   - Check WordPress site with older version
   - Verify update notification appears
   - Test update process

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

2. **ZIP Structure Incorrect**

   - Verify folder name is `rank-math-api-manager`
   - Check for proper file exclusions
   - Ensure main plugin file is in root of plugin folder

3. **Auto-Update Not Working**
   - Verify ZIP is named exactly `rank-math-api-manager.zip`
   - Check that release is published (not draft)
   - Ensure version number in plugin file matches tag

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
**Version**: 1.0.9
