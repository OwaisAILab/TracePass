# TracePass Phase 6 — Professional Deployment

## Implemented
- REST API under `/api/v1`.
- Public passport API at `/api/v1/public/passports/<passport_code>`.
- Authenticated reporting API at `/api/v1/reports/summary`.
- API health endpoint at `/api/v1/health`.
- Pagination/filtering on product API.
- Pytest baseline for API, authentication protection and public passport visibility.
- PostgreSQL production configuration through `DATABASE_URL`.
- Docker image and Docker Compose deployment with PostgreSQL.
- Environment-variable template for secrets/database configuration.

## Local API examples
```text
GET /api/v1/health
GET /api/v1/products?q=shirt&page=1&per_page=20
GET /api/v1/public/passports/TP-XXXXXXXX
```

The reporting endpoint requires an authenticated administrator or auditor session.

## Production security checklist
- Set a long random `SECRET_KEY`.
- Never commit `.env`, database passwords or uploaded documents.
- Use HTTPS at the reverse proxy.
- Keep `DEBUG=False`.
- Run migrations before application startup.
- Restrict upload types and sizes at the application and reverse-proxy layers.
- Use a dedicated PostgreSQL account with least privilege.
- Back up PostgreSQL and uploaded evidence separately.
- Review audit logs regularly.
