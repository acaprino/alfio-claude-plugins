# Security

Security hardening for RabbitMQ 4.x in production: bootstrap defaults to remove, vhost and topic-permission isolation for multi-tenancy, TLS, and secrets handling. Load this reference when hardening a broker for TLS or multi-tenancy, or when the `rabbitmq-expert` agent's inline first-aid advice needs the exact command syntax.

## Bootstrap hardening

Source: https://www.rabbitmq.com/docs/production-checklist

- Delete the default `guest` user in production. By default it can only connect from `localhost` (its credentials are well known), but hardening removes it outright rather than relying on that restriction.
- Set `anonymous_login_user = none` to turn off anonymous logins entirely.
- Create one user per application. A mobile app, a web app, and a data-aggregation service each get their own credential; never share one login across applications. Per-application users let you correlate connections to the owning app, grant fine-grained permissions per app, and roll over one app's credentials without touching another's.

## Virtual hosts

Source: https://www.rabbitmq.com/docs/production-checklist, https://www.rabbitmq.com/docs/access-control

- One vhost per application or environment for isolation, for example `project1_development` and `project1_production`.
- Permissions are granted per vhost as a triple of regular expressions on named resources: configure, write, and read.
- Grant them with `rabbitmqctl set_permissions -p <vhost> <user> <configure-regex> <write-regex> <read-regex>`.
- Withhold access with an unmatchable pattern (RabbitMQ's own examples use `^$`). Pseudo-example for a publisher-only and a consumer-only user on the same vhost:

  ```
  rabbitmqctl set_permissions -p orders publisher-app "^$" "^orders\..*" "^$"
  rabbitmqctl set_permissions -p orders consumer-app "^$" "^$" "^orders\..*"
  ```

  The publisher-only user has no configure and no read access, only write matching the `orders.` prefix. The consumer-only user is the mirror image: write withheld, read granted on the same prefix.

## Topic permissions

Source: https://www.rabbitmq.com/docs/access-control

- Topic exchanges get an additional, opt-in authorization layer on top of the vhost triple above. It does nothing until an administrator defines topic permissions for a specific exchange.
- `rabbitmqctl set_topic_permissions` restricts publish and consume on a topic exchange by routing-key pattern. The routing-key check runs only after the base `basic.publish` permission already allows the call, and is never reached if that check refuses access first. The access-control guide itself points to the `rabbitmqctl` man page for the full argument list rather than inlining an example, so confirm the exact argument order there before scripting it.
- Patterns support variable expansion for `username`, `vhost`, and `client_id`, so one topic-permission rule can scope many tenants on a shared topic exchange instead of giving each tenant a separate exchange.

## TLS

Source: https://www.rabbitmq.com/docs/production-checklist

- Enable TLS on every listener that crosses a public or shared network. RabbitMQ's own guidance: use TLS connections when possible, at least to encrypt traffic.
- Turn on peer verification so the client checks the server's certificate and hostname rather than accepting whatever certificate is presented.
- Evaluate the deployed TLS configuration with `testssl.sh`.
- Where TLS is mandated, disable the plain AMQP listener so there is no unencrypted fallback path.

## Secrets

- Never put credentials in files tracked by version control. Inject them through environment variables or a secret store (a Kubernetes `Secret`, Vault).
- Rotate credentials on any suspected or confirmed compromise.
- The management UI and the management HTTP API authenticate with the same user credentials. Scope monitoring access with the `monitoring` tag instead of `administrator`. Source: https://www.rabbitmq.com/docs/access-control, whose documented pattern for a cluster-wide, read-only monitoring user is:

  ```
  default_users.monitoring.vhost_pattern = .*
  default_users.monitoring.tags = monitoring
  default_users.monitoring.configure = ^$
  default_users.monitoring.write = ^$
  default_users.monitoring.read = .*
  ```
