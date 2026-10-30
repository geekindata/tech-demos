# resources

`demo_policy.json` is a compute policy definition, created with the CLI or the UI (it is not a bundle resource):

```bash
databricks cluster-policies create --json @demo_policy.json --profile <your-profile>
```

`node_type_id` is fixed at `Standard_DS3_v2`, which is an **Azure-only** VM type. On AWS or GCP, change it to a node type from `databricks clusters list-node-types` (for example `m5.xlarge` on AWS or `n2-standard-4` on GCP) before creating the policy.
