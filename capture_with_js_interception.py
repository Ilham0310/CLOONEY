#!/usr/bin/env python3
"""
Enhanced capture script that intercepts JavaScript fetch/XHR calls and WebSockets.
This will catch API calls that Playwright's network monitoring might miss.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page

async def capture_with_js_interception():
    """Capture network traffic with JavaScript interception."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        network_logs = []
        js_api_calls = []
        
        # Inject JavaScript to intercept fetch and XHR
        await page.add_init_script("""
        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            const options = args[1] || {};
            const method = options.method || 'GET';
            const body = options.body || '';
            
            // Log to console
            console.log('[FETCH INTERCEPT]', method, url);
            if (body) {
                console.log('[FETCH BODY]', typeof body === 'string' ? body.substring(0, 500) : JSON.stringify(body).substring(0, 500));
            }
            
            // Also store in window for later retrieval
            if (!window.__apiCalls) window.__apiCalls = [];
            window.__apiCalls.push({
                type: 'fetch',
                method: method,
                url: url,
                body: typeof body === 'string' ? body : JSON.stringify(body),
                timestamp: new Date().toISOString()
            });
            
            return originalFetch.apply(this, args);
        };
        
        // Intercept XMLHttpRequest
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            const originalOpen = xhr.open;
            const originalSend = xhr.send;
            
            xhr.open = function(method, url, ...rest) {
                this._method = method;
                this._url = url;
                console.log('[XHR INTERCEPT]', method, url);
                return originalOpen.apply(this, [method, url, ...rest]);
            };
            
            xhr.send = function(data) {
                if (data) {
                    console.log('[XHR BODY]', typeof data === 'string' ? data.substring(0, 500) : JSON.stringify(data).substring(0, 500));
                }
                
                if (!window.__apiCalls) window.__apiCalls = [];
                window.__apiCalls.push({
                    type: 'xhr',
                    method: this._method,
                    url: this._url,
                    body: typeof data === 'string' ? data : JSON.stringify(data),
                    timestamp: new Date().toISOString()
                });
                
                return originalSend.apply(this, arguments);
            };
            
            return xhr;
        };
        
        // Monitor WebSocket connections
        const originalWebSocket = window.WebSocket;
        window.WebSocket = function(url, protocols) {
            console.log('[WEBSOCKET]', url, protocols);
            
            if (!window.__apiCalls) window.__apiCalls = [];
            window.__apiCalls.push({
                type: 'websocket',
                url: url,
                protocols: protocols,
                timestamp: new Date().toISOString()
            });
            
            const ws = new originalWebSocket(url, protocols);
            
            ws.addEventListener('open', () => {
                console.log('[WEBSOCKET OPEN]', url);
            });
            
            ws.addEventListener('message', (event) => {
                const data = event.data;
                console.log('[WEBSOCKET MESSAGE]', url, data.substring(0, 500));
                
                // Parse and store full message
                try {
                    const parsed = JSON.parse(data);
                    if (!window.__apiCalls) window.__apiCalls = [];
                    window.__apiCalls.push({
                        type: 'websocket_message',
                        url: url,
                        message: parsed,
                        raw: data,
                        timestamp: new Date().toISOString()
                    });
                } catch (e) {
                    // Not JSON, store as string
                    if (!window.__apiCalls) window.__apiCalls = [];
                    window.__apiCalls.push({
                        type: 'websocket_message',
                        url: url,
                        message: data,
                        raw: data,
                        timestamp: new Date().toISOString()
                    });
                }
            });
            
            ws.addEventListener('error', (event) => {
                console.log('[WEBSOCKET ERROR]', url, event);
            });
            
            return ws;
        };
        """)
        
        # Listen to console messages
        def handle_console(msg):
            text = msg.text
            if any(keyword in text for keyword in ['FETCH', 'XHR', 'WEBSOCKET']):
                print(f"  📝 JS: {text}")
                if 'INTERCEPT' in text or 'WEBSOCKET' in text:
                    js_api_calls.append({
                        'timestamp': datetime.now().isoformat(),
                        'message': text
                    })
        
        page.on("console", handle_console)
        
        # Also capture network requests
        async def log_request(request):
            url = request.url
            method = request.method
            
            if 'asana.com' in url and any(keyword in url for keyword in ['/api/', 'graphql', 'projects', 'tasks']):
                print(f"\n🌐 NETWORK: {method} {url}")
                if request.post_data:
                    print(f"   Body: {request.post_data[:300]}")
        
        page.on("request", log_request)
        
        print("=" * 80)
        print("ENHANCED CAPTURE WITH JS INTERCEPTION")
        print("=" * 80)
        print("\n1. Navigating to Asana...")
        await page.goto("https://app.asana.com")
        await asyncio.sleep(3)
        
        print("\n2. Please log in manually...")
        print("   (Watch the console for intercepted API calls)")
        input("   Press Enter after you've logged in...")
        
        print("\n3. IMPORTANT: Now perform CRUD operations!")
        print("   - Create a new project")
        print("   - Create a task in that project")
        print("   - Edit the task")
        print("   - Delete the task")
        print("\n   Watch the console output for intercepted API calls...")
        print("   (This will run for 90 seconds - please perform operations NOW)")
        
        # Periodically check for JS API calls
        async def check_js_calls():
            for _ in range(18):  # 90 seconds / 5 seconds
                await asyncio.sleep(5)
                try:
                    api_calls = await page.evaluate("window.__apiCalls || []")
                    if api_calls:
                        print(f"\n📊 Found {len(api_calls)} JS API calls so far...")
                        for call in api_calls[-5:]:  # Show last 5
                            print(f"   {call['type'].upper()}: {call['method']} {call.get('url', 'N/A')}")
                except:
                    pass
        
        await asyncio.gather(
            asyncio.sleep(90),
            check_js_calls()
        )
        
        # Get final JS API calls
        try:
            final_api_calls = await page.evaluate("window.__apiCalls || []")
            js_api_calls.extend(final_api_calls)
        except:
            pass
        
        print("\n" + "=" * 80)
        print("CAPTURE COMPLETE")
        print("=" * 80)
        print(f"\nJavaScript API calls intercepted: {len(js_api_calls)}")
        
        # Filter for Asana API calls
        asana_calls = [c for c in js_api_calls if 'asana.com' in str(c.get('url', ''))]
        
        # Extract WebSocket messages
        ws_messages = [c for c in js_api_calls if c.get('type') == 'websocket_message' and 'sync.app.asana.com' in str(c.get('url', ''))]
        
        # Look for CRUD operations in WebSocket messages
        crud_operations = []
        for msg in ws_messages:
            message_data = msg.get('message', {})
            if isinstance(message_data, list):
                for item in message_data:
                    msg_type = item.get('msg', '')
                    if msg_type in ['added', 'changed', 'removed', 'committed', 'batch_removed']:
                        crud_operations.append({
                            'operation': msg_type,
                            'collection': item.get('collection', ''),
                            'id': item.get('id', ''),
                            'fields': item.get('fields', {}),
                            'timestamp': msg.get('timestamp', '')
                        })
            elif isinstance(message_data, dict):
                msg_type = message_data.get('msg', '')
                if msg_type in ['added', 'changed', 'removed', 'committed', 'batch_removed']:
                    crud_operations.append({
                        'operation': msg_type,
                        'collection': message_data.get('collection', ''),
                        'id': message_data.get('id', ''),
                        'fields': message_data.get('fields', {}),
                        'timestamp': msg.get('timestamp', '')
                    })
        
        print(f"\nAsana API calls: {len(asana_calls)}")
        print(f"WebSocket messages: {len(ws_messages)}")
        print(f"CRUD operations found: {len(crud_operations)}")
        
        if crud_operations:
            print("\n✅ CRUD Operations Found in WebSocket Messages:")
            collections = {}
            for op in crud_operations:
                coll = op.get('collection', 'unknown')
                if coll not in collections:
                    collections[coll] = []
                collections[coll].append(op.get('operation'))
            
            for coll, ops in collections.items():
                print(f"   📦 {coll}: {', '.join(set(ops))}")
            
            print(f"\n   Sample operations:")
            for op in crud_operations[:10]:
                print(f"      {op['operation'].upper()}: {op['collection']} (id: {str(op['id'])[:50]})")
        else:
            print("\n⚠️  No CRUD operations found in WebSocket messages")
            print("   But WebSocket connection was detected - operations may have happened before capture")
        
        # Save results
        output = {
            'js_api_calls': js_api_calls,
            'websocket_messages': ws_messages,
            'crud_operations': crud_operations,
            'summary': {
                'total_js_calls': len(js_api_calls),
                'asana_calls': len(asana_calls),
                'websocket_messages': len(ws_messages),
                'crud_operations': len(crud_operations)
            }
        }
        
        with open('js_api_capture.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✅ Saved to js_api_capture.json")
        print("\nPlease review the console output above to see what API calls were intercepted.")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(capture_with_js_interception())

