#!/usr/bin/env python3
"""Share Zotero's heavy runtime while keeping stdio clients and libraries separate."""
from collections.abc import MutableMapping
from contextvars import ContextVar
import fcntl
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import socket
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid

UPSTREAM = Path.home() / '.local/share/uv/tools/zotero-mcp-server/bin/zotero-mcp'
CPU_LIMITS = ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')


class SessionExpired(RuntimeError):
    pass


class ClientLibrary(MutableMapping):
    """A library override shared by one client's requests, including worker threads."""
    def __init__(self):
        self._state = ContextVar('zotero_client_library', default=None)

    def bind(self, state):
        return self._state.set(state)

    def reset(self, token):
        self._state.reset(token)

    def _current(self):
        state = self._state.get()
        if state is None:
            state = {}
            self._state.set(state)
        return state

    def __getitem__(self, key):
        return self._current()[key]

    def __setitem__(self, key, value):
        self._current()[key] = value

    def __delitem__(self, key):
        del self._current()[key]

    def __iter__(self):
        return iter(self._current())

    def __len__(self):
        return len(self._current())


def private_directory(path):
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError('Zotero runtime directory is not private and owned by this user')
    return path


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path, timeout=180):
        super().__init__('localhost', timeout=timeout)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(self.path))


class Bridge:
    def __init__(self, path):
        self.path = path
        self.client_id = uuid.uuid4().hex
        self.session_id = None
        self.protocol = '2024-11-05'

    def request(self, payload):
        connection = UnixHTTPConnection(self.path, timeout=180 if 'id' in payload else 5)
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                   'X-Zotero-Client': self.client_id, 'MCP-Protocol-Version': self.protocol}
        if self.session_id:
            headers['Mcp-Session-Id'] = self.session_id
        try:
            connection.request('POST', '/mcp', json.dumps(payload).encode(), headers)
            response = connection.getresponse()
            data = response.read()
            if response.status == 404 and self.session_id:
                raise SessionExpired('Zotero session expired; reconnect this MCP client. The request was not replayed.')
            if response.status not in (200, 202):
                raise RuntimeError(f'Zotero backend returned HTTP {response.status}; request was not replayed')
            self.session_id = response.getheader('Mcp-Session-Id') or self.session_id
            result = json.loads(data) if data else None
            if payload.get('method') == 'initialize' and result:
                self.protocol = result.get('result', {}).get('protocolVersion', self.protocol)
            return result
        finally:
            connection.close()

    def close(self):
        if self.session_id:
            connection = UnixHTTPConnection(self.path, timeout=2)
            try:
                connection.request('DELETE', '/mcp', headers={
                    'Mcp-Session-Id': self.session_id, 'X-Zotero-Client': self.client_id,
                    'MCP-Protocol-Version': self.protocol})
                connection.getresponse().read()
            except (OSError, http.client.HTTPException):
                pass
            finally:
                connection.close()


def configuration_key(environment, config):
    # Index progress is data, not a different server configuration. Otherwise
    # each successful sync would create a second daemon with another model.
    config = json.loads(json.dumps(config))
    semantic = config.get('semantic_search', {})
    if isinstance(semantic, dict):
        updates = semantic.get('update_config', {})
        if isinstance(updates, dict):
            updates.pop('last_update', None)
        for key in ('last_sync_version', 'last_sync_versions', 'index_schema_version', 'backfill_unattributed'):
            semantic.pop(key, None)
    referenced = set()

    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('api_key_env_var'), str):
                referenced.add(value['api_key_env_var'])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(config)
    relevant = {key: value for key, value in environment.items()
                if key.startswith(('ZOTERO_', 'CHROMA_', 'FASTMCP_', 'OPENAI_', 'OLLAMA_',
                                   'GEMINI_', 'GOOGLE_', 'HF_', 'XDG_', 'TORCH_', 'TOKENIZERS_'))
                or key in referenced
                or key in CPU_LIMITS
                or key.upper() in ('UNSAFE_OPERATIONS', 'UNPAYWALL_EMAIL', 'HTTPS_PROXY',
                                   'HTTP_PROXY', 'ALL_PROXY', 'NO_PROXY', 'SSL_CERT_FILE',
                                   'SSL_CERT_DIR', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE')}
    signature = json.dumps([relevant, config], sort_keys=True).encode()
    # A changed adapter must never silently attach to an older daemon.
    signature += Path(__file__).read_bytes()
    return hashlib.sha256(signature).hexdigest()[:20]


def runtime_directory():
    # CLI environment discovery is lightweight; server/model imports stay in the daemon.
    # Upstream __init__.py eagerly imports server even for a cli submodule import.
    # The stdio bridge only needs the CLI's environment resolver. The separate
    # backend interpreter still imports and registers the complete upstream package.
    if 'zotero_mcp' not in sys.modules:
        package = importlib.util.find_spec('zotero_mcp')
        sys.modules['zotero_mcp'] = importlib.util.module_from_spec(package)
    # Match client.py's load_dotenv() search without importing its heavy dependencies.
    from dotenv import load_dotenv
    client_file = Path(importlib.util.find_spec('zotero_mcp.client').origin)
    for parent in client_file.parents:
        candidate = parent / '.env'
        if candidate.is_file():
            load_dotenv(candidate)
            break
    from zotero_mcp.cli import setup_zotero_environment
    setup_zotero_environment()
    for name in CPU_LIMITS:
        os.environ.setdefault(name, '2')
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    config_path = Path.home() / '.config/zotero-mcp/config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    key = configuration_key(os.environ, config)
    root = private_directory(Path('/tmp') / f'zotero-mcp-{os.getuid()}')
    return private_directory(root / key)


def ready(path):
    connection = UnixHTTPConnection(path, timeout=1)
    try:
        connection.request('GET', '/health')
        response = connection.getresponse()
        return response.status == 200 and response.read() == b'zotero-shared-v1'
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def ensure_backend(directory):
    path = directory / 'server.sock'
    with open(directory / 'start.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if ready(path):
            return path
        # The daemon holds its own lock for its entire lifetime. A slow start
        # cannot cause a second model process after a client startup timeout.
        with open(directory / 'server.lock', 'a') as server_lock:
            try:
                fcntl.flock(server_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                running = False
            except BlockingIOError:
                running = True
        if not running:
            with open(directory / 'server.log', 'ab') as log:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                            '--backend', str(directory)],
                                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                           stderr=log, start_new_session=True)
        deadline = time.monotonic() + 50
        while time.monotonic() < deadline:
            if ready(path):
                return path
            if not running and process.poll() is not None:
                raise RuntimeError('Zotero shared backend failed to start; inspect its private server.log')
            time.sleep(0.1)
        raise RuntimeError('Zotero shared backend is still starting; no duplicate server was started')


class ClientScope:
    def __init__(self, app, libraries):
        self.app = app
        self.libraries = libraries
        self.clients = {}

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        if scope['path'] == '/health':
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'zotero-shared-v1'})
            return
        client_id = dict(scope['headers']).get(b'x-zotero-client', b'').decode('ascii', errors='ignore')
        if len(client_id) != 32 or any(c not in '0123456789abcdef' for c in client_id):
            await send({'type': 'http.response.start', 'status': 400, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'Missing client identity'})
            return
        now = time.monotonic()
        self.clients = {key: entry for key, entry in self.clients.items() if now - entry[0] < 600}
        state = self.clients.get(client_id, (now, {}))[1]
        self.clients[client_id] = (now, state)
        token = self.libraries.bind(state)
        try:
            await self.app(scope, receive, send)
        finally:
            self.libraries.reset(token)
            if scope['method'] == 'DELETE':
                self.clients.pop(client_id, None)


def run_backend(directory):
    import uvicorn
    private_directory(directory)
    with open(directory / 'server.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        from zotero_mcp import client
        from zotero_mcp.server import mcp
        from zotero_mcp.cli import _warmup_reranker_in_background
        from zotero_mcp.toolsets import apply_toolsets
        import fastmcp.server.http as http_transport
        manager_class = http_transport.FastMCPStreamableHTTPSessionManager

        class ExpiringSessionManager(manager_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.session_idle_timeout = 300

            async def handle_request(self, scope, receive, send):
                try:
                    return await super().handle_request(scope, receive, send)
                finally:
                    if scope.get('method') == 'DELETE':
                        session_id = dict(scope.get('headers', [])).get(b'mcp-session-id', b'').decode()
                        transport = self._server_instances.get(session_id)
                        if transport is not None and transport.is_terminated:
                            self._server_instances.pop(session_id, None)
                            self._session_owners.pop(session_id, None)

        # The installed MCP SDK supports leases; FastMCP does not expose the option.
        http_transport.FastMCPStreamableHTTPSessionManager = ExpiringSessionManager
        libraries = ClientLibrary()
        client._active_library_override = libraries
        # This private socket has the same user boundary as the original stdio server.
        apply_toolsets(mcp, transport='stdio')
        _warmup_reranker_in_background()
        app = ClientScope(mcp.http_app(path='/mcp', json_response=True), libraries)
        path = directory / 'server.sock'
        path.unlink(missing_ok=True)
        (directory / 'server.pid').write_text(str(os.getpid()))
        uvicorn.run(app, uds=str(path), log_level='warning', access_log=False)


def run_stdio(path):
    bridge = Bridge(path)
    output_lock = threading.Lock()
    slots = threading.BoundedSemaphore(4)
    stopping = threading.Event()

    def heartbeat():
        while not stopping.wait(60):
            if bridge.session_id:
                try:
                    bridge.request({'jsonrpc': '2.0', 'id': f'keepalive-{uuid.uuid4().hex}', 'method': 'ping'})
                except SessionExpired:
                    print('Zotero session expired; reconnect this MCP client.', file=sys.stderr, flush=True)
                    os.kill(os.getpid(), signal.SIGTERM)
                    return
                except Exception:
                    continue

    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    old_signal = signal.signal(signal.SIGTERM, terminate)
    threading.Thread(target=heartbeat, daemon=True).start()

    def respond(payload):
        expired = False
        try:
            result = bridge.request(payload)
        except Exception as error:
            expired = isinstance(error, SessionExpired)
            result = {'jsonrpc': '2.0', 'id': payload.get('id'),
                      'error': {'code': -32000, 'message': str(error)}}
        if 'id' in payload and result is not None:
            with output_lock:
                print(json.dumps(result), flush=True)
        if expired:
            os.kill(os.getpid(), signal.SIGTERM)

    def worker(payload):
        try:
            respond(payload)
        finally:
            slots.release()

    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload.get('method') == 'initialize' or 'id' not in payload:
                respond(payload)
            else:
                if slots.acquire(blocking=False):
                    threading.Thread(target=worker, args=(payload,), daemon=True).start()
                else:
                    with output_lock:
                        print(json.dumps({'jsonrpc': '2.0', 'id': payload['id'], 'error': {
                            'code': -32000, 'message': 'Four Zotero requests are already running; retry shortly'}}), flush=True)
    finally:
        stopping.set()
        bridge.close()
        signal.signal(signal.SIGTERM, old_signal)


def main():
    os.umask(0o077)
    arguments = sys.argv[1:]
    if len(arguments) == 2 and arguments[0] == '--backend':
        run_backend(Path(arguments[1]))
    elif arguments in (['serve'], ['serve', '--transport', 'stdio'], ['serve', '-t', 'stdio']):
        run_stdio(ensure_backend(runtime_directory()))
    else:
        os.execv(str(UPSTREAM), [str(UPSTREAM), *arguments])


if __name__ == '__main__':
    main()
