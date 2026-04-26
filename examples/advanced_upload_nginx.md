# Advanced upload behind nginx

This example runs `exphttp` behind an nginx reverse proxy. The server keeps
user file access limited to `<root>/uploads/` by default, while advanced
upload accepts payloads through JSON body, headers, or URL parameters.

## 1. Start the server

```bash
exphttp \
  --host 127.0.0.1 \
  --port 18080 \
  --dir /srv/exphttp \
  --auth 'agent:<strong-password>' \
  --quiet
```

Uploaded files are written to `/srv/exphttp/uploads/`.

## 2. nginx configuration

```nginx
server {
    listen 443 ssl http2;
    server_name files.example.com;

    ssl_certificate     /etc/letsencrypt/live/files.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/files.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:18080;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;

        # Preserve uncommon HTTP methods used by advanced upload.
        proxy_method       $request_method;

        client_max_body_size   200m;
        proxy_read_timeout     300s;
        proxy_send_timeout     300s;
    }
}
```

## 3. Client side

```bash
PAYLOAD=$(base64 -w0 report.pdf)

curl -X CHECKDATA https://files.example.com/ \
     -u agent:<strong-password> \
     -H "Content-Type: application/json" \
     -d "{\"d\":\"${PAYLOAD}\",\"n\":\"report.pdf\"}"
```

Header transport is also supported:

```bash
curl -X CHECKDATA https://files.example.com/ \
     -u agent:<strong-password> \
     -H "X-D: ${PAYLOAD}" \
     -H "X-N: report.pdf"
```

## Caveats

- Always layer TLS + Basic Auth on externally reachable deployments.
- Prefer JSON body transport for sensitive data; headers and URLs are more
  likely to appear in proxy logs.
