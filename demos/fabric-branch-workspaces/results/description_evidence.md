# demo_report description evidence

Read-only calls, Oct 30, 2026. IDs masked to all zeros, workspace names generic.
The workspace exports return an all-zero logicalId themselves; the Git logicalId is a real value and is masked here.

Finding: Git and the feature workspace carry the description "One card report on demo_model"; the main workspace item has an empty description, so its export has no description line.

## GET items, main workspace

```json
{
  "type": "Report",
  "displayName": "demo_report",
  "description": ""
}
```

## GET items, feature workspace

```json
{
  "type": "Report",
  "displayName": "demo_report",
  "description": "One card report on demo_model"
}
```

## .platform, main workspace

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "Report",
    "displayName": "demo_report"
  },
  "config": {
    "version": "2.0",
    "logicalId": "00000000-0000-0000-0000-000000000000"
  }
}
```

## .platform, feature workspace

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "Report",
    "displayName": "demo_report",
    "description": "One card report on demo_model"
  },
  "config": {
    "version": "2.0",
    "logicalId": "00000000-0000-0000-0000-000000000000"
  }
}
```

## .platform, Git, branch fabric-demo-git

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "Report",
    "displayName": "demo_report",
    "description": "One card report on demo_model"
  },
  "config": {
    "version": "2.0",
    "logicalId": "00000000-0000-0000-0000-000000000000"
  }
}
```

## Diff, Git vs main workspace .platform (masked)

```diff
--- git/.platform
+++ main-workspace/.platform
@@ -2,8 +2,7 @@
   "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
   "metadata": {
     "type": "Report",
-    "displayName": "demo_report",
-    "description": "One card report on demo_model"
+    "displayName": "demo_report"
   },
   "config": {
     "version": "2.0",
```
