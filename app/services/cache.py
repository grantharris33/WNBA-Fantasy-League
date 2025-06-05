"""
Cache service for managing API response caching and statistics.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import ApiCache, CacheStatistics

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing API response caching."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key.

        Args:
            key: Cache key

        Returns:
            Cached data if found and not expired, None otherwise
        """
        try:
            cache_entry = self.db.query(ApiCache).filter(ApiCache.cache_key == key).first()

            if not cache_entry:
                self._record_cache_miss(key)
                return None

            if cache_entry.is_expired():
                # Clean up expired entry
                self.db.delete(cache_entry)
                self.db.commit()
                self._record_cache_miss(key)
                return None

            # Update hit statistics
            cache_entry.increment_hit_count()
            self.db.commit()
            self._record_cache_hit(key, cache_entry.endpoint)

            return cache_entry.data

        except Exception as e:
            logger.error(f"Error getting cache entry for key {key}: {e}")
            self.db.rollback()
            return None

    def set(self, key: str, data: Dict[str, Any], ttl_seconds: int = 3600, endpoint: Optional[str] = None) -> bool:
        """
        Set cached data.

        Args:
            key: Cache key
            data: Data to cache
            ttl_seconds: Time to live in seconds (default 1 hour)
            endpoint: API endpoint this cache is for

        Returns:
            True if successful, False otherwise
        """
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

            # Calculate approximate size
            size_bytes = len(json.dumps(data, default=str))

            # Check if entry already exists
            existing = self.db.query(ApiCache).filter(ApiCache.cache_key == key).first()

            if existing:
                # Update existing entry
                existing.data = data
                existing.expires_at = expires_at
                existing.size_bytes = size_bytes
                existing.endpoint = endpoint
            else:
                # Create new entry
                cache_entry = ApiCache(
                    cache_key=key, data=data, expires_at=expires_at, endpoint=endpoint, size_bytes=size_bytes
                )
                self.db.add(cache_entry)

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error setting cache entry for key {key}: {e}")
            self.db.rollback()
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a cache entry.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False if not found or error
        """
        try:
            cache_entry = self.db.query(ApiCache).filter(ApiCache.cache_key == key).first()
            if cache_entry:
                self.db.delete(cache_entry)
                self.db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting cache entry for key {key}: {e}")
            self.db.rollback()
            return False

    def clear_expired(self) -> int:
        """
        Clear all expired cache entries.

        Returns:
            Number of entries cleared
        """
        try:
            now = datetime.utcnow()
            expired_entries = self.db.query(ApiCache).filter(ApiCache.expires_at < now).all()
            count = len(expired_entries)

            for entry in expired_entries:
                self.db.delete(entry)

            self.db.commit()
            logger.info(f"Cleared {count} expired cache entries")
            return count

        except Exception as e:
            logger.error(f"Error clearing expired cache entries: {e}")
            self.db.rollback()
            return 0

    def get_cache_stats(self, date: Optional[datetime] = None) -> Optional[CacheStatistics]:
        """
        Get cache statistics for a specific date.

        Args:
            date: Date to get stats for (defaults to today)

        Returns:
            Cache statistics or None if not found
        """
        if date is None:
            date = datetime.utcnow().date()
        else:
            date = date.date() if isinstance(date, datetime) else date

        return self.db.query(CacheStatistics).filter(CacheStatistics.date == date).first()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get general cache information.

        Returns:
            Dictionary with cache metrics
        """
        try:
            total_entries = self.db.query(func.count(ApiCache.id)).scalar() or 0
            total_size = self.db.query(func.sum(ApiCache.size_bytes)).scalar() or 0

            now = datetime.utcnow()
            expired_count = self.db.query(func.count(ApiCache.id)).filter(ApiCache.expires_at < now).scalar() or 0

            # Get hit counts
            hit_stats = self.db.query(
                func.sum(ApiCache.hit_count).label('total_hits'), func.avg(ApiCache.hit_count).label('avg_hits')
            ).first()

            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'expired_entries': expired_count,
                'active_entries': total_entries - expired_count,
                'total_hits': hit_stats.total_hits or 0,
                'average_hits_per_entry': round(hit_stats.avg_hits or 0, 2),
            }

        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {}

    def _record_cache_hit(self, key: str, endpoint: Optional[str] = None):
        """Record a cache hit in daily statistics."""
        try:
            self._update_daily_stats(cache_hit=True, endpoint=endpoint)
        except Exception:
            # Don't let statistics tracking interfere with cache operations
            pass

    def _record_cache_miss(self, key: str, endpoint: Optional[str] = None):
        """Record a cache miss in daily statistics."""
        try:
            self._update_daily_stats(cache_hit=False, endpoint=endpoint)
        except Exception:
            # Don't let statistics tracking interfere with cache operations
            pass

    def _update_daily_stats(self, cache_hit: bool, endpoint: Optional[str] = None):
        """Update daily cache statistics."""
        try:
            today = datetime.utcnow().date()
            stats = self.db.query(CacheStatistics).filter(CacheStatistics.date == today).first()

            if not stats:
                stats = CacheStatistics(date=today)
                self.db.add(stats)
                self.db.flush()  # Make sure the stats record exists

            stats.total_requests = (stats.total_requests or 0) + 1
            if cache_hit:
                stats.cache_hits = (stats.cache_hits or 0) + 1
                stats.api_calls_saved = (stats.api_calls_saved or 0) + 1
            else:
                stats.cache_misses = (stats.cache_misses or 0) + 1

            # Update endpoint-specific stats
            if endpoint:
                endpoint_stats = stats.endpoint_stats or {}
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = {'hits': 0, 'misses': 0}

                if cache_hit:
                    endpoint_stats[endpoint]['hits'] += 1
                else:
                    endpoint_stats[endpoint]['misses'] += 1

                stats.endpoint_stats = endpoint_stats

            self.db.commit()

        except Exception as e:
            logger.error(f"Error updating daily cache stats: {e}")
            self.db.rollback()

    def create_cache_key(self, endpoint: str, **params) -> str:
        """
        Create a standardized cache key.

        Args:
            endpoint: API endpoint
            **params: Parameters to include in key

        Returns:
            Cache key string
        """
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params if v is not None)

        if param_str:
            return f"{endpoint}?{param_str}"
        return endpoint

    def cache_decorator(self, ttl_seconds: int = 3600, key_func: Optional[callable] = None):
        """
        Decorator for caching function results.

        Args:
            ttl_seconds: Time to live in seconds
            key_func: Function to generate cache key from function args
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function and cache result
                result = func(*args, **kwargs)
                if result is not None:
                    self.set(cache_key, result, ttl_seconds, endpoint=func.__name__)

                return result

            return wrapper

        return decorator
