# Story 1: Fix Critical Frontend-Backend Integration Issues

**Priority**: P0 - Critical Path
**Dependencies**: None

## Overview
The frontend and backend are not properly integrated, causing runtime errors and poor user experience. This story addresses critical integration issues that prevent the MVP from functioning correctly.

## Acceptance Criteria
1. All API calls from frontend successfully reach backend endpoints
2. WebSocket connections work in both development and production
3. Type definitions match between frontend and backend
4. Proper error handling for all API calls
5. Environment variables properly configured

## Technical Tasks

### 1. Fix API Base URL Configuration
- [ ] Update frontend to use `VITE_API_URL` environment variable consistently
- [ ] Remove all hardcoded `localhost:8000` references
- [ ] Create proper axios instance with base URL configuration
- [ ] Update all API calls to use the configured instance

### 2. Fix WebSocket Configuration
- [ ] Update frontend to use `VITE_WS_URL` environment variable
- [ ] Fix WebSocket URL construction for draft and live game connections
- [ ] Add proper reconnection logic with exponential backoff
- [ ] Handle authentication for WebSocket connections
- [ ] Add a pong to the server pings and automatically remove stale connections

### 3. Synchronize Type Definitions
- [ ] Compare all TypeScript interfaces with Pydantic schemas
- [ ] Update frontend types to match backend exactly
- [ ] Create shared type definitions for common models
- [ ] Add type generation script from OpenAPI schema

### 4. Fix Missing/Mismatched Endpoints (8 hours)
- [ ] Create `/api/v1/weekly-bonus-winners` endpoint
- [ ] Fix avatar deletion endpoint to accept DELETE method
- [ ] Add system stats endpoints for admin dashboard
- [ ] Ensure all frontend API calls have corresponding backend endpoints

### 5. Standardize Error Handling
- [ ] Create consistent error response format in backend
- [ ] Update frontend to handle standardized error responses
- [ ] Add proper error boundaries in React
- [ ] Implement user-friendly error messages

### 6. Fix Authentication Flow
- [ ] Ensure JWT tokens are properly stored and sent
- [ ] Fix WebSocket authentication using query parameters
- [ ] Add token refresh mechanism
- [ ] Handle 401 errors with redirect to login

## Testing Requirements
- [ ] Integration tests for all API endpoints
- [ ] WebSocket connection tests
- [ ] Error handling tests
- [ ] Environment configuration tests

## Documentation Updates
- [ ] Document all environment variables
- [ ] Create API integration guide
- [ ] Document WebSocket protocol
- [ ] Add troubleshooting guide

## Definition of Done
- All frontend pages load without console errors
- API calls succeed with proper data
- WebSocket connections establish and maintain connection remove stale connections
- Works in both development and production environments
- All tests pass
- All linters/formatters pass