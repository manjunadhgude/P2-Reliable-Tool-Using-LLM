# Security and threat model

## Protected boundaries

- A signed, expiring token is minted for a fixed local demo identity. Roles and tenant are reloaded from the database.
- Orders, conversations and pending actions are scoped to the authenticated tenant/user. Unknown and out-of-scope orders return the same safe message.
- Tool names/actions are allowlisted. Pydantic rejects unknown fields. Business rules and decimal calculations run in Python. There is no model-visible SQL, shell, arbitrary Python or HTTP tool.
- Ticket proposals remain pending; only a supervisor/admin approval endpoint inserts a ticket. A unique idempotency key makes approval replay safe.
- Data is synthetic. No payment, email or external action exists. Traces do not persist hidden model reasoning.

## Local demo limitations

Demo tokens are not a production identity provider. Set `DEMO_SIGNING_SECRET`, restrict CORS, enforce HTTPS, configure database least privilege, add rate/body-size limits, and integrate an identity provider before deployment. Seeded supervisor/evaluator personas are available in the demo UI.

Threats considered include direct prompt injection, injected tool text, unsupported tools, malformed JSON, extra fields, cross-tenant access, unauthorized/replayed approvals, duplicate writes, and refund issuance requests. Prompts label untrusted content; server checks remain the security boundary.
