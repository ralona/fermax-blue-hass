# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2025-01-14

### Fixed
- **Spanish API Responses**: Enhanced response validation to properly recognize Spanish success messages like "la puerta abierta"
- **Response Logging**: Changed unclear responses from ERROR to WARNING level since they still succeed

### Technical Improvements
- Added Spanish success indicators: "abierta", "abierto", "puerta abierta"
- Added Spanish error indicators: "cerrada", "bloqueada"

## [2.1.0] - 2025-01-14

### Fixed
- **Token Expiration**: Fixed issue where integration would fail after ~1 week due to expired tokens
- **Token Refresh**: Implemented proactive token refresh 5 minutes before expiration
- **API Response Validation**: Improved door open response validation to detect "KO" errors correctly
- **Error Messages**: Added user-friendly error messages in Spanish for common failures

### Added
- **Token Persistence**: Tokens are now stored persistently and survive Home Assistant restarts
- **Enhanced Logging**: Added detailed debug logging for troubleshooting authentication issues
- **Automatic Token Renewal**: Coordinator now automatically renews tokens during updates
- **Better Error Handling**: Improved error handling throughout the integration

### Changed
- **Update Interval**: Reduced from 30 to 15 minutes for faster detection of issues
- **Authentication Flow**: Enhanced with retry logic and better error recovery
- **Door Open Logic**: Now properly validates API responses instead of assuming success

### Technical Improvements
- Added `_needs_refresh()` method with 5-minute buffer before token expiration
- Implemented token storage using Home Assistant's Store helper
- Enhanced error propagation from API to UI with specific error types
- Improved logging throughout authentication and API call flow

## [2.0.0] - 2025-01-13

### Added
- Enhanced device naming with telefonillo identification
- Improved door device detection and naming

## [1.0.0] - 2025-01-16

### Added
- Initial release of Fermax Blue Home Assistant integration
- Email/password authentication via config flow
- Automatic device discovery for doors and access points
- Button entities for door control ("Open Door" action)
- HACS compatibility for easy installation and updates
- Support for multiple door devices per home
- Robust error handling and token refresh
- Spanish and English translations
- Comprehensive documentation and installation guide

### Features
- **Authentication**: Secure credential storage with automatic token refresh
- **Device Discovery**: Automatically finds all paired doors and access points
- **Door Control**: Individual button entities for each door
- **Home Assistant Integration**: Native UI integration with device registry
- **Multi-language Support**: English and Spanish translations
- **HACS Support**: Easy installation via Home Assistant Community Store

### Technical Details
- Uses Fermax Blue API v2 endpoints
- Implements async/await patterns for Home Assistant compatibility
- Proper device and entity management
- Coordinator pattern for efficient API usage
- Comprehensive error handling and logging

### Configuration
- Simple setup through Home Assistant UI
- Validates credentials during setup
- Automatic device discovery after authentication
- No manual configuration required

## [1.1.0] - 2025-01-16

### Changed
- Complete rewrite of API client with real Fermax Blue endpoints
- Implemented OAuth2 authentication flow
- Updated to use actual API structure from reverse-engineered app
- Improved error handling and logging
- Fixed authentication issues

### Fixed
- Authentication now uses correct OAuth flow
- API endpoints match actual Fermax Blue service
- Proper handling of access tokens and refresh tokens
- Device discovery now uses pairings endpoint

### Technical Changes
- Uses OAuth endpoint: `https://oauth.blue.fermax.com/oauth/token`
- Implements proper headers mimicking iOS app
- AccessId structure matches API requirements
- Token refresh mechanism implemented

## [2.0.0] - 2025-07-24

### Added
- **Enhanced Device Naming**: Devices now display "Device Name Door Name" format
- **Multi-Intercom Support**: Perfect identification for users with multiple telefonillos
- **Improved Device Organization**: Each intercom is properly identified by its configured name

### Changed
- Device names now combine intercom name with door name (e.g., "Telefonillo Casa 1 Portal")
- Removed hyphen from device names for cleaner appearance
- Updated device hierarchy to better reflect multiple building/property setups

### Technical Changes
- Modified `fermax_integration.py` to include device name in door naming
- Updated `button.py` to use device-specific identification
- Enhanced device info structure for better Home Assistant integration

## [Unreleased]

### Planned
- Add support for additional Fermax Blue features
- Implement device status monitoring
- Add automation triggers for door events
- Enhanced error recovery and offline handling
- Additional language translations