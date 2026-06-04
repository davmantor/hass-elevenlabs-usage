#!/bin/bash
# Deploy hass-elevenlabs-usage to local Home Assistant config
set -e

SRC="$(dirname "$0")/custom_components/hass_elevenlabs_usage"
# Update this path to match your HA custom_components directory:
DEST="/config/custom_components/hass_elevenlabs_usage"

sudo cp "$SRC"/__init__.py "$SRC"/config_flow.py "$SRC"/const.py "$SRC"/manifest.json "$SRC"/sensor.py "$SRC"/strings.json "$DEST"/
sudo mkdir -p "$DEST/translations"
sudo cp "$SRC"/translations/en.json "$DEST/translations/"
sudo mkdir -p "$DEST/brand"
sudo cp "$SRC"/brand/icon.png "$SRC"/brand/logo.png "$DEST/brand/"

echo "Deployed to $DEST"
