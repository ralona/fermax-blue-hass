# Fermax Blue Home Assistant Integration

A custom Home Assistant integration for controlling Fermax Blue intercom doors through their API.

## Features

- **Easy Configuration**: Simple email/password setup through Home Assistant UI
- **Device Discovery**: Automatically discovers your home and door devices
- **Door Control**: Individual button entities for each door with "Open Door" action
- **HACS Compatible**: Can be installed and updated through HACS

## Installation

### HACS (Recommended)

1. In HACS, go to "Integrations"
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/ralona/fermax-blue-hass` as an Integration
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the files
3. Copy the `custom_components/fermax_blue` folder to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

## Configuration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Fermax Blue"
4. Enter your Fermax Blue app credentials:
   - **Email**: Your Fermax Blue account email
   - **Password**: Your Fermax Blue account password
5. Click **Submit**

The integration will automatically discover your home and door devices.

## Usage

After configuration, you will see:

- **Home Device**: Your main dwelling/home
- **Door Devices**: Individual devices for each door/access point
- **Button Entities**: "Open Door" buttons for each door

### Using the Door Buttons

- In the Home Assistant UI, you can press the "Open Door" button for any door
- Buttons can be used in automations and scripts
- Each button press will authenticate with Fermax Blue and open the specified door

### Example Automation

```yaml
automation:
  - alias: "Open Main Door at 8 AM"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.main_door_open_door
```

## Device Structure

The integration creates the following device hierarchy:

```
Fermax Blue Home
├── Main Door
│   └── Open Door (Button)
├── Garage Door
│   └── Open Door (Button)
└── Back Door
    └── Open Door (Button)
```

## Troubleshooting

### Authentication Issues

- Verify your email and password are correct
- Check that your Fermax Blue account is active
- Ensure you have proper permissions to control the doors

### Connection Problems

- Check your internet connection
- Verify that Fermax Blue services are operational
- Look at Home Assistant logs for detailed error messages

### Device Not Appearing

- Restart the integration: **Settings** → **Devices & Services** → **Fermax Blue** → **⋮** → **Reload**
- Check logs for API errors
- Verify your account has access to the devices

## API Information

This integration uses the Fermax Blue API to:
- Authenticate with your account credentials
- Discover available devices and doors
- Send door open commands

API calls are made over HTTPS and include proper authentication tokens.

## Support

For issues and feature requests, please visit the [GitHub Issues](https://github.com/ralona/fermax-blue-hass/issues) page.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Based on the excellent work by [marcosav](https://github.com/marcosav/fermax-blue-intercom) for understanding the Fermax Blue API.