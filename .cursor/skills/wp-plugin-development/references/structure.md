# Plugin structure and loading

Use this file when introducing or refactoring a plugin architecture.

## Core concepts

- Main plugin file contains the plugin header and bootstraps the plugin.
- Use the plugin slug as the naming root for namespaces, functions, hooks, handles, options, and REST namespaces.
- Prefer predictable init:
  - minimal boot file
  - a loader/class that registers hooks
  - admin-only code behind admin hooks

Upstream reference:

- https://developer.wordpress.org/plugins/plugin-basics/

