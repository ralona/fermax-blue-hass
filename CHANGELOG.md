# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Planned
- Add support for additional Fermax Blue features
- Implement device status monitoring
- Add automation triggers for door events
- Enhanced error recovery and offline handling
- Additional language translations