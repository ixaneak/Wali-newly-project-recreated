"""
Optimized Database Connection Pooling for WALI Micro-Insurance

CIMA Production Requirements:
- 10,000 concurrent users
- 100 transactions/minute
- 5-year data retention
- 99.9% uptime

Fly.io PostgreSQL Default: 100 connections total
Distribution across services:
  - policy-service: 30 connections
  - claims-service: 30 connections  
  - payment-gateway: 20 connections
  - ai-concierge: 15 connections
  - compliance: 5 connections

Pooling Strategy:
  - Client-side (QueuePool): Default for most services
  - Server-side (PgBouncer): Recommended for high-throughput scenarios
"""

import os
import logging
from sqlalchemy import create_engine, event, QueuePool, NullPool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Optional

logger = logging.getLogger('db_pool')


# ═════════════════════════════════════════════════════════════════
# POOL CONFIGURATION
# ═════════════════════════════════════════════════════════════════

POOL_CONFIGS = {
    'policy-service': {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    },
    'claims-service': {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    },
    'payment-gateway': {
        'pool_size': 8,
        'max_overflow': 12,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    },
    'ai-concierge': {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    },
    'compliance': {
        'pool_size': 3,
        'max_overflow': 2,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    },
}


def should_use_server_side_pooler() -> bool:
    """
    Check if we should disable client-side pooling.
    
    When using PgBouncer or similar server-side poolers,
    we should use NullPool on the client side to avoid
    double-pooling issues.
    
    Returns:
        True if DATABASE_URL points to a pooler
    """
    db_url = os.getenv('DATABASE_URL', '')
    pooler_indicators = [
        'pgbouncer',
        'pooler',
        '6432',  # PgBouncer default port
        'supabase.co',  # Supabase uses pooler
    ]
    return any(indicator in db_url.lower() for indicator in pooler_indicators)


def get_pool_class():
    """
    Get the appropriate pool class based on configuration.
    
    Returns:
        QueuePool for client-side pooling
        NullPool when using server-side pooler (PgBouncer)
    """
    if should_use_server_side_pooler():
        logger.info("Server-side pooler detected (PgBouncer). Using NullPool on client.")
        return NullPool
    
    logger.info("Using client-side QueuePool")
    return QueuePool


# ═════════════════════════════════════════════════════════════════
# ENGINE FACTORY
# ═════════════════════════════════════════════════════════════════

def create_engine_with_pool(database_url: str, service_name: str = None) -> Engine:
    """
    Create SQLAlchemy engine with optimized connection pooling.
    
    Automatically detects and configures for:
    - Client-side pooling (QueuePool) - DEFAULT
    - Server-side pooling (PgBouncer) - Auto-detected
    
    Args:
        database_url: PostgreSQL connection URL
        service_name: Service identifier for pool configuration
        
    Returns:
        Configured SQLAlchemy Engine
    """
    service = service_name or os.getenv('SERVICE_NAME', 'unknown')
    config = POOL_CONFIGS.get(service, {
        'pool_size': 5,
        'max_overflow': 5,
        'pool_timeout': 30,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    })
    
    # Determine pool class based on environment
    pool_class = get_pool_class()
    
    # Build engine arguments
    engine_kwargs = {
        'poolclass': pool_class,
        'echo': False,
        'connect_args': {
            "sslmode": "require",
            "connect_timeout": 10,
            "application_name": service,
        }
    }
    
    # Only add pool-specific args for QueuePool
    if pool_class is QueuePool:
        engine_kwargs.update({
            'pool_size': config['pool_size'],
            'max_overflow': config['max_overflow'],
            'pool_timeout': config['pool_timeout'],
            'pool_recycle': config['pool_recycle'],
            'pool_pre_ping': config['pool_pre_ping'],
        })
    else:
        # For NullPool (server-side pooler), we still want pre-ping
        engine_kwargs['pool_pre_ping'] = True
    
    engine = create_engine(database_url, **engine_kwargs)
    
    # Attach monitoring events
    _attach_pool_events(engine, service, pool_class)
    
    if pool_class is QueuePool:
        logger.info(
            f"[QueuePool] Database pool created for {service}: "
            f"size={config['pool_size']}, max_overflow={config['max_overflow']}"
        )
    else:
        logger.info(
            f"[NullPool] Database engine created for {service} "
            f"(server-side pooler detected)"
        )
    
    return engine


def _attach_pool_events(engine: Engine, service_name: str, pool_class):
    """Attach monitoring events to connection pool."""
    
    @event.listens_for(engine, 'checkout')
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout for monitoring."""
        pool = engine.pool
        if hasattr(pool, 'size'):  # Only QueuePool has these attributes
            logger.debug(
                f"[{service_name}] Connection checked out. "
                f"Pool: size={pool.size()}, checked_in={pool.checkedin()}, "
                f"checked_out={pool.checkedout()}, overflow={pool.overflow()}"
            )
        else:
            logger.debug(f"[{service_name}] Connection checked out (server-side pooled)")
    
    @event.listens_for(engine, 'checkin')
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection checkin for monitoring."""
        logger.debug(f"[{service_name}] Connection checked in")
    
    @event.listens_for(engine, 'connect')
    def receive_connect(dbapi_conn, connection_record):
        """Log new connection creation."""
        logger.debug(f"[{service_name}] New database connection created")


# ═════════════════════════════════════════════════════════════════
# SERVER-SIDE POOLER SUPPORT (PgBouncer)
# ═════════════════════════════════════════════════════════════════

def create_pgbouncer_engine(database_url: str, service_name: str = None) -> Engine:
    """
    Create engine specifically for PgBouncer connection.
    
    PgBouncer Configuration Notes:
    - Use NullPool on client side (PgBouncer handles pooling)
    - Use 'transaction' pooling mode for most services
    - Use 'session' pooling mode if using prepared statements
    - Disable SQLAlchemy's pre-ping if using PgBouncer's pooler
    
    Args:
        database_url: PgBouncer connection URL (port 6432)
        service_name: Service identifier
        
    Returns:
        Configured SQLAlchemy Engine with NullPool
    """
    service = service_name or os.getenv('SERVICE_NAME', 'unknown')
    
    engine = create_engine(
        database_url,
        poolclass=NullPool,  # PgBouncer handles pooling
        echo=False,
        pool_pre_ping=True,  # Still validate connections
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
            "application_name": service,
            # PgBouncer-specific options
            "options": "-c statement_timeout=30000",  # 30s query timeout
        }
    )
    
    _attach_pool_events(engine, service, NullPool)
    
    logger.info(
        f"[PgBouncer] Database engine created for {service} "
        f"(using server-side pooling)"
    )
    
    return engine


def get_connection_string_for_pooler(original_url: str, pooler_type: str = 'pgbouncer') -> str:
    """
    Convert direct PostgreSQL URL to pooler URL.
    
    Args:
        original_url: Original PostgreSQL connection URL
        pooler_type: Type of pooler ('pgbouncer', 'supabase', etc.)
        
    Returns:
        Modified connection string for pooler
    """
    from urllib.parse import urlparse, urlunparse
    
    parsed = urlparse(original_url)
    
    if pooler_type == 'pgbouncer':
        # Change port to PgBouncer port (6432)
        netloc = f"{parsed.hostname}:6432"
        if parsed.username:
            netloc = f"{parsed.username}:{parsed.password}@{netloc}"
        
        return urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
    
    elif pooler_type == 'supabase':
        # Supabase pooler uses specific format
        # postgresql://postgres.[project]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
        return original_url  # Assume already in pooler format
    
    return original_url


# ═════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═════════════════════════════════════════════════════════════════

class DatabaseManager:
    """
    Database manager with optimized session handling.
    
    Automatically detects and configures for client-side or server-side pooling.
    
    Usage:
        # Client-side pooling (default)
        db = DatabaseManager(database_url, 'policy-service')
        
        # Server-side pooling (auto-detected from URL)
        db = DatabaseManager('postgres://...pgbouncer...:6432/...', 'policy-service')
        
        # Context manager (recommended)
        with db.session() as session:
            result = session.query(Model).all()
    """
    
    def __init__(self, database_url: str, service_name: str = None):
        self.service_name = service_name or os.getenv('SERVICE_NAME', 'unknown')
        self.database_url = database_url
        self.engine = create_engine_with_pool(database_url, self.service_name)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def session(self):
        """Context manager for database sessions."""
        return SessionContext(self.SessionLocal)
    
    def get_pool_status(self) -> dict:
        """Get current connection pool status."""
        pool = self.engine.pool
        
        # QueuePool has detailed stats
        if hasattr(pool, 'size'):
            return {
                'service': self.service_name,
                'pool_type': 'QueuePool (client-side)',
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'total_connections': pool.checkedin() + pool.checkedout(),
            }
        else:
            # NullPool (server-side pooler)
            return {
                'service': self.service_name,
                'pool_type': 'NullPool (server-side pooler)',
                'note': 'Connection pooling handled by PgBouncer/server-side pooler',
            }
    
    def close(self):
        """Close all connections in the pool."""
        self.engine.dispose()
        logger.info(f"[{self.service_name}] Database pool closed")


class SessionContext:
    """Context manager for database sessions."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None
    
    def __enter__(self):
        self.session = self.session_factory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


# ═════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═════════════════════════════════════════════════════════════════

def check_database_health(engine: Engine) -> dict:
    """
    Check database connectivity and pool health.
    
    Returns:
        dict with health status and pool statistics
    """
    try:
        # Test connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        pool = engine.pool
        result = {
            'status': 'healthy',
            'error': None,
        }
        
        # Add pool stats if available (QueuePool)
        if hasattr(pool, 'size'):
            result.update({
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
            })
        else:
            result['pool_type'] = 'server-side (NullPool)'
        
        return result
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
        }


# ═════════════════════════════════════════════════════════════════
# FASTAPI DEPENDENCY
# ═════════════════════════════════════════════════════════════════

def get_db_dependency(db_manager: DatabaseManager):
    """
    Create FastAPI dependency for database sessions.
    
    Usage:
        db = DatabaseManager(database_url, 'policy-service')
        get_db = get_db_dependency(db)
        
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    def get_db():
        session = db_manager.get_session()
        try:
            yield session
        finally:
            session.close()
    return get_db


# ═════════════════════════════════════════════════════════════════
# POOLING BEST PRACTICES DOCUMENTATION
# ═════════════════════════════════════════════════════════════════

"""
CONNECTION POOLING BEST PRACTICES

1. Client-Side Pooling (QueuePool) - DEFAULT
   - Use for: Most applications, development, testing
   - Pros: Full control, detailed metrics, no external dependencies
   - Cons: Uses more database connections
   - Configuration: pool_size=10, max_overflow=20

2. Server-Side Pooling (PgBouncer) - PRODUCTION HIGH-SCALE
   - Use for: >1000 concurrent connections, microservices architecture
   - Pros: Lower connection overhead, connection multiplexing
   - Cons: Additional infrastructure, less visibility
   - Setup: 
     * Install PgBouncer
     * Configure pooling mode (transaction/session)
     * Set SQLAlchemy to use NullPool
   
3. Connection Pool Sizing
   - Formula: connections = (core_count * 2) + effective_spindle_count
   - For 100 connections max across 5 services: 20 per service
   - Adjust based on actual load patterns

4. Monitoring
   - Track: pool utilization, checkout time, overflow events
   - Alert if: >80% pool utilization, checkout time >1s

5. Environment Variables
   - DATABASE_URL: Standard PostgreSQL URL
   - SERVICE_NAME: Identifies service for pool config
   - POOL_SIZE: Override default pool size
   - MAX_OVERFLOW: Override default overflow

EXAMPLE CONFIGURATIONS

# Development (client-side pooling)
DATABASE_URL=postgresql://user:pass@localhost:5432/wali
SERVICE_NAME=policy-service

# Production with PgBouncer (server-side pooling)
DATABASE_URL=postgresql://user:pass@pgbouncer.internal:6432/wali
SERVICE_NAME=policy-service
# Automatically uses NullPool

# Supabase with pooler
DATABASE_URL=postgresql://postgres.xxx:[password]@aws-0-xx.pooler.supabase.com:6543/postgres
SERVICE_NAME=policy-service
# Automatically uses NullPool
"""
