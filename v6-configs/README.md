# Vantage6 demo configs (reference)

In your current setup you used:

- `v6 server start` with config name: `serverdemo`
- `v6 node start` with config name: `nodedemo`

Those configs are created by the `v6 dev create-demo-network` command and are stored in your Vantage6 config directory (usually under `~/.config/vantage6/`).

This folder is included so you have a single place in the repo to keep **exported copies** of those configs.

## How to export your running configs into this repo

On Himalaya:

```bash
# find the config files created by v6
ls -R ~/.config/vantage6/
# copy them into this repo folder (example)
cp -v ~/.config/vantage6/server/serverdemo.yaml ./v6-configs/
cp -v ~/.config/vantage6/node/nodedemo.yaml ./v6-configs/
```

Then re-zip and share the repo.
