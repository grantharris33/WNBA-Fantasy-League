# Story 8: Production Deployment Configuration

**Priority**: P0 - Critical Path  
**Effort**: 2-3 days  
**Dependencies**: Story 1 (Integration fixes)

## Overview
The application needs proper production configuration including environment setup, security hardening, monitoring, and automated deployment to be MVP-ready.

## Acceptance Criteria
1. Environment-specific configurations properly separated
2. Security best practices implemented
3. Monitoring and logging configured
4. Automated backup system in place
5. Zero-downtime deployment process
6. Performance optimizations applied

## Technical Tasks

### Environment Configuration (8 hours)

#### 1. Create Environment Templates (2 hours)
```bash
# Create environment files
- [ ] .env.development - Development settings
- [ ] .env.staging - Staging environment
- [ ] .env.production - Production settings
- [ ] .env.example - Template with all variables
```

#### 2. Backend Configuration Updates (3 hours)
```python
# app/core/config.py
- [ ] Add environment-specific settings
- [ ] Validate all required env vars on startup
- [ ] Add configuration for different databases
- [ ] Configure CORS for production domains
- [ ] Set up proper logging levels
```

#### 3. Frontend Configuration (3 hours)
```typescript
// frontend/src/config/
- [ ] environment.ts - Environment detection
- [ ] api.config.ts - API URL configuration
- [ ] features.config.ts - Feature flags
```

### Security Hardening (8 hours)

#### 1. Backend Security (4 hours)
```python
# Security implementations
- [ ] Add rate limiting middleware
- [ ] Implement request size limits
- [ ] Add SQL injection prevention
- [ ] Configure secure headers
- [ ] Add input sanitization
- [ ] Implement CSRF protection
```

#### 2. Frontend Security (2 hours)
```typescript
// Security measures
- [ ] Content Security Policy headers
- [ ] XSS prevention
- [ ] Secure cookie handling
- [ ] Environment variable validation
```

#### 3. Infrastructure Security (2 hours)
```yaml
# docker-compose.prod.yml
- [ ] Use secrets management
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS properly
- [ ] Implement fail2ban
```

### Monitoring and Logging (6 hours)

#### 1. Application Monitoring (3 hours)
```python
# app/core/monitoring.py
- [ ] Add health check endpoints
- [ ] Implement metrics collection
- [ ] Add performance monitoring
- [ ] Create status dashboard endpoint
```

#### 2. Logging Configuration (3 hours)
```python
# Structured logging
- [ ] Configure JSON logging
- [ ] Add request ID tracking
- [ ] Implement log rotation
- [ ] Set up error alerting
- [ ] Add audit logging
```

### Database and Backup (4 hours)

#### 1. Database Optimization (2 hours)
```sql
-- Performance optimizations
- [ ] Add missing indexes
- [ ] Optimize slow queries
- [ ] Configure connection pooling
- [ ] Set up read replicas (future)
```

#### 2. Backup System (2 hours)
```bash
# scripts/backup.sh
- [ ] Automated daily backups
- [ ] Backup rotation (keep 30 days)
- [ ] Backup verification
- [ ] Restore procedures
- [ ] Off-site backup storage
```

### Deployment Automation (6 hours)

#### 1. Docker Configuration (3 hours)
```dockerfile
# Dockerfile.prod
- [ ] Multi-stage builds
- [ ] Security scanning
- [ ] Minimal base images
- [ ] Non-root user
- [ ] Health checks
```

#### 2. CI/CD Pipeline (3 hours)
```yaml
# .github/workflows/deploy.yml
- [ ] Automated testing
- [ ] Security scanning
- [ ] Build and push images
- [ ] Blue-green deployment
- [ ] Rollback capability
```

## Configuration Files

### Production Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:pass@db:5432/wnba_prod
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<generate-strong-key>
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60

# Frontend
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
VITE_ENVIRONMENT=production
VITE_SENTRY_DSN=<sentry-dsn>
```

### Monitoring Endpoints
```python
# Health checks
GET /health - Basic health check
GET /health/detailed - Detailed system status
GET /metrics - Prometheus metrics
GET /api/v1/status - Application status
```

## Performance Optimizations
- [ ] Enable gzip compression
- [ ] Configure CDN for static assets
- [ ] Implement Redis caching
- [ ] Database query optimization
- [ ] Frontend bundle optimization
- [ ] Image optimization

## Security Checklist
- [ ] All secrets in environment variables
- [ ] HTTPS enforced everywhere
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens implemented
- [ ] Dependency scanning enabled
- [ ] Security updates automated

## Deployment Process
1. Run tests in CI
2. Build Docker images
3. Push to registry
4. Deploy to staging
5. Run smoke tests
6. Deploy to production
7. Monitor for issues

## Rollback Plan
- Keep previous version tagged
- Database migration rollback scripts
- Quick switch via load balancer
- Backup restore procedures

## Definition of Done
- All environments properly configured
- Security scan shows no high vulnerabilities
- Monitoring dashboards operational
- Automated backups running
- Deployment completes in <10 minutes
- Zero-downtime deployment verified
- Performance benchmarks met
- All security measures implemented