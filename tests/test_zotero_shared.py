"""Isolation and transport checks for the shared local Zotero server."""
import asyncio
import importlib.util
import io
import json
import os
from pathlib import Path
import socketserver
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'scripts/zotero_shared.py'
spec = importlib.util.spec_from_file_location('zotero_shared', PATH)
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)


class LibraryIsolationTest(unittest.IsolatedAsyncioTestCase):
    async def test_library_switch_stays_with_client_across_worker_threads(self):
        libraries = shared.ClientLibrary()
        first, second = {}, {}

        async def client(state, value):
            token = libraries.bind(state)
            try:
                def switch():
                    libraries['library_id'] = value
                    libraries['library_type'] = 'group'
                await asyncio.to_thread(switch)
                await asyncio.sleep(0)
                self.assertEqual(dict(libraries), {'library_id': value, 'library_type': 'group'})
            finally:
                libraries.reset(token)

        await asyncio.gather(client(first, 'a'), client(second, 'b'))
        token = libraries.bind(first)
        try:
            libraries.clear()
        finally:
            libraries.reset(token)
        self.assertEqual(first, {})
        self.assertEqual(second['library_id'], 'b')


class TransportTest(unittest.TestCase):
    def test_index_timestamp_does_not_create_another_model_process(self):
        first = {'semantic_search': {'update_config': {'auto_update': False, 'last_update': '2026-08-27'}}}
        second = {'semantic_search': {'update_config': {'auto_update': False, 'last_update': '2026-09-09'}}}
        second['semantic_search'].update(last_sync_version=77, last_sync_versions={'0': 77}, index_schema_version=2, backfill_unattributed=0)
        self.assertEqual(shared.configuration_key({}, first), shared.configuration_key({}, second))
        self.assertEqual(first['semantic_search']['update_config']['last_update'], '2026-08-27')

    def test_expired_session_does_not_replay_a_write(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                requests.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(404)
                self.send_header('Content-Length', '0')
                self.end_headers()

        with tempfile.TemporaryDirectory(prefix='zs-', dir='/tmp') as directory:
            path = Path(directory) / 'server.sock'
            server = socketserver.UnixStreamServer(str(path), Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                bridge = shared.Bridge(path)
                bridge.session_id = 'expired'
                with self.assertRaises(shared.SessionExpired):
                    bridge.request({'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call', 'params': {
                        'name': 'zotero_create_item', 'arguments': {}}})
                self.assertEqual(len(requests), 1)
            finally:
                server.shutdown()
                server.server_close()

    def test_cancellation_passes_four_running_calls_and_eof_closes_session(self):
        cancelled, closed, started = threading.Event(), threading.Event(), threading.Event()
        count = 0
        lock = threading.Lock()

        class FakeBridge:
            session_id = None

            def __init__(self, path):
                pass

            def request(self, payload):
                nonlocal count
                if payload['method'] == 'tools/call':
                    with lock:
                        count += 1
                        if count == 4:
                            started.set()
                    cancelled.wait(2)
                elif payload['method'] == 'notifications/cancelled':
                    cancelled.set()

            def close(self):
                closed.set()

        def lines():
            for index in range(4):
                yield json.dumps({'jsonrpc': '2.0', 'id': index, 'method': 'tools/call'})
            self.assertTrue(started.wait(1))
            yield json.dumps({'jsonrpc': '2.0', 'method': 'notifications/cancelled', 'params': {'requestId': 0}})
            self.assertTrue(cancelled.wait(0.2))

        with patch.object(shared, 'Bridge', FakeBridge), patch.object(shared.sys, 'stdin', lines()), patch.object(shared.sys, 'stdout', io.StringIO()):
            shared.run_stdio(Path('/unused-test-socket'))
        self.assertTrue(closed.is_set())

    def test_provider_credentials_and_custom_key_never_share_backend(self):
        config = {'semantic_search': {'embedding_config': {'api_key_env_var': 'MY_EMBEDDING_KEY'}}}
        base = shared.configuration_key({}, config)
        for key in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_BASE_URL', 'MY_EMBEDDING_KEY', 'ZOTERO_API_KEY'):
            value = shared.configuration_key({key: 'private-value'}, config)
            self.assertNotEqual(base, value, key)
            self.assertNotIn('private-value', value)
        self.assertEqual(base, shared.configuration_key({'CODEX_THREAD_ID': 'another-client'}, config))

    def test_separate_clients_keep_http_sessions_and_response_ids(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                seen.append((self.headers.get('Mcp-Session-Id'), self.headers['X-Zotero-Client']))
                session = self.headers.get('Mcp-Session-Id') or self.headers['X-Zotero-Client']
                body = json.dumps({'jsonrpc': '2.0', 'id': payload['id'], 'result': {'session': session}}).encode()
                self.send_response(200)
                self.send_header('Mcp-Session-Id', session)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        with tempfile.TemporaryDirectory(prefix='zs-', dir='/tmp') as directory:
            path = Path(directory) / 'server.sock'
            server = socketserver.UnixStreamServer(str(path), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                a, b = shared.Bridge(path), shared.Bridge(path)
                for client in (a, b, a, b):
                    response = client.request({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'})
                    self.assertEqual(response['id'], 1)
                    self.assertEqual(response['result']['session'], client.client_id)
                self.assertNotEqual(a.client_id, b.client_id)
                self.assertIsNone(seen[0][0])
                self.assertEqual(seen[2][0], a.client_id)
            finally:
                server.shutdown()
                server.server_close()

    def test_private_runtime_rejects_symlink(self):
        with tempfile.TemporaryDirectory(prefix='zs-', dir='/tmp') as directory:
            path = Path(directory) / 'alias'
            path.symlink_to(directory)
            with self.assertRaises(RuntimeError):
                shared.private_directory(path)


if __name__ == '__main__':
    unittest.main()
