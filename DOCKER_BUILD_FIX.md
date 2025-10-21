# Docker Build Cache Export Fix

## Problem Summary
The GitHub Actions workflow is failing with the error:
```
ERROR: failed to build: Cache export is not supported for the docker driver.
```

This occurs because the workflow is trying to use GitHub Actions cache (`type=gha`) with the default Docker driver, which doesn't support cache export functionality.

## Root Cause
- The default `docker` driver only supports local builds and doesn't support advanced caching features
- GitHub Actions cache requires a driver that supports cache import/export (like `docker-container` or `buildkit`)
- The workflow was missing the Docker Buildx setup step in the deploy workflow

## Solutions

### Solution 1: Add Docker Buildx Setup (RECOMMENDED) ✅
**Implementation:** Add `docker/setup-buildx-action` before building
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
  with:
    driver-opts: image=moby/buildkit:latest
```

**Pros:**
- ✅ Enables advanced caching features
- ✅ Supports multi-platform builds
- ✅ Faster builds with cache reuse
- ✅ Reduces GitHub Actions minutes usage
- ✅ Standard approach used by most projects

**Cons:**
- ❌ Slightly increases workflow complexity
- ❌ Adds ~10-15 seconds to setup time

### Solution 2: Remove GitHub Actions Cache
**Implementation:** Remove `cache-from` and `cache-to` parameters
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    # Remove these lines:
    # cache-from: type=gha
    # cache-to: type=gha,mode=max
```

**Pros:**
- ✅ Simplest fix
- ✅ No additional setup required
- ✅ Works with default Docker driver

**Cons:**
- ❌ No build caching (slower builds)
- ❌ Increased GitHub Actions minutes usage
- ❌ Rebuilds entire image every time
- ❌ Higher bandwidth usage

### Solution 3: Use Registry Cache
**Implementation:** Use Docker registry for caching
```yaml
cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
```

**Pros:**
- ✅ Works across different CI systems
- ✅ Cache persists in registry
- ✅ Can be shared across branches

**Cons:**
- ❌ Uses registry storage space
- ❌ Requires Buildx setup anyway
- ❌ Slightly slower than GHA cache

### Solution 4: Use Inline Cache
**Implementation:** Embed cache in the image
```yaml
cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
cache-to: type=inline
```

**Pros:**
- ✅ No separate cache storage needed
- ✅ Simple to implement

**Cons:**
- ❌ Increases image size
- ❌ Less efficient than dedicated cache
- ❌ Still requires Buildx

## Applied Fix
We've implemented **Solution 1** by adding the Docker Buildx setup step to the deploy.yml workflow. This is the industry-standard approach that provides the best balance of performance and maintainability.

## Testing
After pushing these changes, the workflow should:
1. Set up Docker Buildx with the container driver
2. Use GitHub Actions cache for faster builds
3. Successfully build and push the Docker image

## Additional Notes
- The CI workflow (ci.yml) already had Docker Buildx setup, which is why it wasn't failing
- The deploy workflow was missing this critical step
- This fix maintains consistency across both workflows
