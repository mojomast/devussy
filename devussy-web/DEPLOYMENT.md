# VPS Deployment Checklist for v0.4.0

## Pre-Deployment Checks

### 1. Environment Variables
- [ ] Copy `.env.example` to `.env` in `devussy-web/`
- [ ] Set `REQUESTY_API_KEY`
- [ ] Set `STREAMING_SECRET` (used by nginx and backend)
- [ ] Configure `NEXT_PUBLIC_IRC_WS_URL` (default: `wss://dev.ussy.host/irc`)
- [ ] Configure `NEXT_PUBLIC_IRC_CHANNEL` (default: `#devussy-chat`)

### 2. SSL Certificates
- [ ] Verify Let's Encrypt certificates exist at `/etc/letsencrypt/`
- [ ] Check certificate validity: `sudo certbot certificates`
- [ ] Renew if needed: `sudo certbot renew`

### 3. Docker Images
- [ ] Pull latest code: `git pull origin adaptive-llm-clean`
- [ ] Stop existing containers: `docker-compose -f docker-compose.prod.yml down`
- [ ] Remove old images (optional): `docker system prune -a`

## Deployment Steps

### 1. Build and Start Services
```bash
cd devussy/devussy-web
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Verify Services
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f streaming-server
docker-compose -f docker-compose.prod.yml logs -f nginx

# Test endpoints
curl http://localhost:3000  # Should return Next.js HTML
curl http://localhost:8000/api/models  # Should return JSON with models
```

### 3. Test Frontend Features
- [ ] Visit https://dev.ussy.host
- [ ] Test theme switching (Bliss, Terminal, Default)
- [ ] Open new project window - verify redesigned UI
- [ ] Test model settings - verify theme support
- [ ] Test IRC connection (should connect to WebSocket)
- [ ] Create a test project through the pipeline

## Common Issues & Fixes

### Issue: Frontend build fails with NEXT_PUBLIC_* errors
**Fix**: Ensure build args are set in docker-compose.prod.yml:
```yaml
build:
  args:
    NEXT_PUBLIC_IRC_WS_URL: ${NEXT_PUBLIC_IRC_WS_URL:-wss://dev.ussy.host/irc}
    NEXT_PUBLIC_IRC_CHANNEL: ${NEXT_PUBLIC_IRC_CHANNEL:-#devussy-chat}
```

### Issue: Theme not persisting after refresh
**Fix**: This is expected - themes are stored in localStorage. Check browser console for errors.

### Issue: IRC not connecting
**Check**:
1. WebSocket URL is correct in environment
2. InspIRCd is running
3. nginx is properly proxying WebSocket connections
4. Check nginx config for `/irc` location

### Issue: Streaming server crashes with asyncio errors
**Fix**: This was fixed in v0.4.0. If still occurring:
1. Ensure you're using the latest code
2. Check logs: `docker-compose -f docker-compose.prod.yml logs streaming-server`
3. Restart: `docker-compose -f docker-compose.prod.yml restart streaming-server`

### Issue: "No space left on device"
**Fix**: Clean up Docker:
```bash
docker system prune -a --volumes
docker volume prune
```

## Post-Deployment Verification

### Functionality Tests
- [ ] New project window displays correctly with new design
- [ ] Theme switching works (check all three themes)
- [ ] Model settings dropdown shows proper theming
- [ ] Can create and run a project through full pipeline
- [ ] Can download artifacts
- [ ] IRC chat connects and sends messages

### Performance Checks
- [ ] Frontend loads in < 3 seconds
- [ ] Streaming responses appear in real-time
- [ ] No console errors in browser dev tools
- [ ] Memory usage stable (check with `docker stats`)

## Rollback Plan

If issues occur:

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Revert code
git checkout <previous-commit>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Log Locations
- **Frontend**: `docker-compose -f docker-compose.prod.yml logs -f frontend`
- **Backend**: `docker-compose -f docker-compose.prod.yml logs -f streaming-server`
- **Nginx**: `docker-compose -f docker-compose.prod.yml logs -f nginx`

### Health Checks
```bash
# Check all services running
docker-compose -f docker-compose.prod.yml ps

# Check resource usage
docker stats

# Check disk space
df -h
```

## Success Criteria

✅ All containers running and healthy
✅ HTTPS working with valid certificates
✅ Frontend accessible at https://dev.ussy.host
✅ New UI features visible and functional
✅ Theme switching works correctly
✅ No errors in logs
✅ Can complete full pipeline workflow

---

**Deployed by**: [Your Name]
**Deployment Date**: [Date]
**Version**: 0.4.0
**Branch**: adaptive-llm-clean
**Commit**: [Git commit hash]
