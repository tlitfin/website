## What this repository is for

Gathering information to get structural biologists oriented on beginning their journey top adopt the most recent and accurate computational tools  

If you're seeing this you're on the coding-style backend. This provides a place to manage code versions, share data, store images, project manage etc, with typical GitHub features.

## Updating WorkflowHub data

After this workflow has been merged into the default branch, the `Update
WorkflowHub data` Action can be run manually from the Actions tab. It
generates and validates `_data/data_workflows.yaml`, builds the Jekyll site, and
opens or updates a pull request when the data changes.

The integration is opt-in and configured in `_config.yml`:

```yaml
workflowhub:
  enabled: true
  base_url: https://workflowhub.eu
  collection_type: space # or collection
  collection_id: 8
  output: _data/data_workflows.yaml
  minimum_record_ratio: 0.8
  # Optional; {workflow_id} is replaced for Galaxy workflows.
  galaxy_launch_url_template: "https://example.org/import?id={workflow_id}"
```

If the block is absent or `enabled` is `false`, the Action completes without
generating data, building the site, or opening a pull request. Command-line
arguments can be used instead of `_config.yml` when running the generator
outside a Jekyll site.

Before the first run on a fork, open **Settings → Actions → General → Workflow
permissions** and allow GitHub Actions to create pull requests.

The workflow is manual-only during the pilot. Add a `schedule` trigger after a
manual update and test deployment have completed successfully.

## Where is the *website*, not just the raw source code?

Point your browser to https://australian-structural-biology-computing.github.io/
