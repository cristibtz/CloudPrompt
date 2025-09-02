# Redis Session Store
import redis
import json
import time
from typing import Dict, Optional, Union
from pathlib import Path
from rich.console import Console
import os

console = Console()

class RedisSessionStore:
    """Production-ready session store with Redis backend and file fallback."""
    
    def __init__(self, redis_url: Optional[str] = None, fallback_to_file: bool = True):
        self.fallback_to_file = fallback_to_file
        self.redis_client = None
        
        # Try to connect to Redis
        if redis_url or os.getenv('REDIS_URL'):
            try:
                self.redis_client = redis.from_url(
                    redis_url or os.getenv('REDIS_URL'),
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                console.print(f"[green]✅ Connected to Redis session store[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Redis unavailable ({e}), using file fallback[/yellow]")
                self.redis_client = None
        
        # File fallback setup
        if self.fallback_to_file:
            self._storage_dir = Path.home() / ".cloudprompt" / "sessions"
            self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_redis_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"cloudprompt:session:{session_id}"
    
    def _get_session_file(self, session_id: str) -> Path:
        """Get file path for session fallback"""
        safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_.")
        return self._storage_dir / f"{safe_session_id}.json"
    
    def load(self, session_id: Optional[str]) -> Dict[str, Union[str, list, dict]]:
        """Load session data from Redis or file fallback"""
        if not session_id:
            return {}
        
        # Try Redis first
        if self.redis_client:
            try:
                data = self.redis_client.hgetall(self._get_redis_key(session_id))
                if data:
                    # Check if tokens have expired (TTL-based)
                    ttl = self.redis_client.ttl(self._get_redis_key(session_id))
                    if ttl > 0:
                        # Deserialize JSON data back to original types
                        deserialized_data = {}
                        for k, v in data.items():
                            try:
                                # Try to parse as JSON first
                                deserialized_data[k] = json.loads(v)
                            except (json.JSONDecodeError, TypeError):
                                # If not JSON, keep as string
                                deserialized_data[k] = v
                        console.print(f"[cyan]📥 Loaded session '{session_id}' from Redis: {list(deserialized_data.keys())} (TTL: {ttl}s)[/cyan]")
                        return deserialized_data
            except Exception as e:
                console.print(f"[yellow]⚠️ Redis load failed: {e}[/yellow]")
        
        # Fallback to file
        if self.fallback_to_file:
            try:
                session_file = self._get_session_file(session_id)
                if session_file.exists():
                    with open(session_file, 'r') as f:
                        file_data = json.load(f)
                        tokens = file_data.get('tokens', {})
                        timestamp = file_data.get('timestamp', time.time())
                        
                        # Check age (30 minutes default expiry)
                        age_minutes = (time.time() - timestamp) / 60
                        if age_minutes < 30:  # 30 minute expiry
                            console.print(f"[cyan]📥 Loaded session '{session_id}' from file: {list(tokens.keys())} (age: {age_minutes:.1f}min)[/cyan]")
                            return tokens
                        else:
                            console.print(f"[yellow]⏰ Session '{session_id}' expired ({age_minutes:.1f}min old)[/yellow]")
            except (json.JSONDecodeError, KeyError, OSError):
                pass
        
        return {}
    
    def save(self, session_id: Optional[str], kv: Dict[str, Union[str, list, dict]], ttl: int = 1800) -> None:
        """Save session data to Redis with TTL and file fallback"""
        if not session_id or not kv:
            return
        
                # Filter out None/empty values and serialize complex types
        filtered_kv = {}
        for k, v in kv.items():
            if v is not None and v != "":
                # Serialize lists and dicts to JSON for Redis storage
                if isinstance(v, (list, dict)):
                    filtered_kv[k] = json.dumps(v)
                else:
                    filtered_kv[k] = str(v)
        if not filtered_kv:
            return
        
        # Try Redis first
        if self.redis_client:
            try:
                redis_key = self._get_redis_key(session_id)
                # Merge with existing data
                existing = self.redis_client.hgetall(redis_key)
                existing.update(filtered_kv)
                
                # Save to Redis with TTL
                self.redis_client.hmset(redis_key, existing)
                self.redis_client.expire(redis_key, ttl)
                
                console.print(f"[cyan]💾 Saved to Redis '{session_id}': {list(filtered_kv.keys())} (TTL: {ttl}s)[/cyan]")
                return
            except Exception as e:
                console.print(f"[yellow]⚠️ Redis save failed: {e}, using file fallback[/yellow]")
        
        # Fallback to file
        if self.fallback_to_file:
            try:
                session_file = self._get_session_file(session_id)
                
                # Load existing data
                existing = {}
                if session_file.exists():
                    with open(session_file, 'r') as f:
                        file_data = json.load(f)
                        existing = file_data.get('tokens', {})
                
                # Merge and save
                existing.update(filtered_kv)
                data = {
                    'tokens': existing,
                    'timestamp': time.time()
                }
                
                with open(session_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                console.print(f"[cyan]💾 Saved to file '{session_id}': {list(filtered_kv.keys())}[/cyan]")
            except OSError as e:
                console.print(f"[red]❌ Failed to save session: {e}[/red]")
    
    def clear_session(self, session_id: Optional[str]) -> None:
        """Clear session data"""
        if not session_id:
            return
        
        # Clear from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(self._get_redis_key(session_id))
                console.print(f"[yellow]🗑️ Cleared Redis session '{session_id}'[/yellow]")
            except Exception:
                pass
        
        # Clear from file
        if self.fallback_to_file:
            try:
                session_file = self._get_session_file(session_id)
                if session_file.exists():
                    session_file.unlink()
                    console.print(f"[yellow]🗑️ Cleared file session '{session_id}'[/yellow]")
            except OSError:
                pass
    
    def list_sessions(self) -> Dict[str, Dict[str, str]]:
        """List all active sessions"""
        sessions = {}
        
        # From Redis
        if self.redis_client:
            try:
                for key in self.redis_client.scan_iter(match="cloudprompt:session:*"):
                    session_id = key.split(":")[-1]
                    data = self.redis_client.hgetall(key)
                    if data:
                        sessions[session_id] = data
            except Exception:
                pass
        
        # From files (if not in Redis)
        if self.fallback_to_file:
            try:
                for session_file in self._storage_dir.glob("*.json"):
                    session_id = session_file.stem
                    if session_id not in sessions:  # Don't override Redis data
                        try:
                            with open(session_file, 'r') as f:
                                file_data = json.load(f)
                                tokens = file_data.get('tokens', {})
                                if tokens:
                                    sessions[session_id] = tokens
                        except (json.JSONDecodeError, KeyError, OSError):
                            continue
            except OSError:
                pass
        
        return sessions
    
    def health_check(self) -> Dict[str, Union[bool, str]]:
        """Check health of session storage"""
        health = {
            "redis_available": False,
            "redis_error": None,
            "file_fallback": self.fallback_to_file,
            "file_writable": False
        }
        
        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                health["redis_available"] = True
            except Exception as e:
                health["redis_error"] = str(e)
        
        # Check file system
        if self.fallback_to_file:
            try:
                test_file = self._storage_dir / ".health_check"
                test_file.write_text("test")
                test_file.unlink()
                health["file_writable"] = True
            except OSError:
                pass
        
        return health
