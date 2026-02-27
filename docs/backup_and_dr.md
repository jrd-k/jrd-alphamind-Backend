# Backup and Disaster Recovery

This document outlines strategies for keeping your data safe and restoring service after failures.

## Database (PostgreSQL)

- **Continuous WAL Archiving**: configure `archive_mode = on` and push WAL files to an S3 bucket or network share. Use tools like `pgbackrest` or `wal-e` for automated archiving and restore.
- **Regular Base Backups**: schedule `pg_basebackup` or use `pgbackrest` to take full backups daily.
- **Encrypted Off‑site Storage**: copy backups to a remote location (AWS S3, Google Cloud Storage, Azure Blob) and enable server-side encryption.
- **Test Restores**: automate periodic restore tests in a staging cluster to verify backup integrity.
- **Point‑in‑Time Recovery (PITR)**: keep WAL archives long enough to roll forward to any moment within retention window.
- **Kubernetes CronJob**: use the `scripts/backup.sh` inside a CronJob container to push dumps to object storage.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pg-backup
  namespace: alphamind
spec:
  schedule: "0 2 * * *"  # 2am daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command: ["/bin/sh","-c","\
              pg_dump $DATABASE_URL -Fc -f /backup/postgres_$(date +%Y%m%d).dump && \
              aws s3 cp /backup/postgres_$(date +%Y%m%d).dump s3://my-bucket/backups/" ]
            envFrom:
              - secretRef:
                  name: alphamind-secrets
            volumeMounts:
              - mountPath: "/backup"
                name: backup-volume
          restartPolicy: OnFailure
          volumes:
            - name: backup-volume
              persistentVolumeClaim:
                claimName: backup-pvc
``` 

## Redis

- **AOF/RDB Persistence**: enable `appendonly yes` and dump every `save` interval. Snapshots are stored locally; back them up along with Postgres dumps.
- **Replication**: run a primary/replica topology so replicas can be promoted if primary fails.
- **Export & Import**: use `redis-cli BGSAVE` + copy `dump.rdb` and `appendonly.aof` files.

## Disaster Recovery Steps

1. **Assess failure**: check which services are down (DB, Redis, app servers).
2. **Failover database**: if using Patroni/HA, let it elect a new leader. For manual recovery, restore latest full backup then replay WALs.
3. **Restore cache**: bring up Redis replica, import persistence files with `redis-cli --pipe` or restart container with `appendonly.aof` present.
4. **Redeploy application**: use `kubectl rollout restart deployment/backend` or `docker stack deploy` as appropriate.
5. **Run health checks**: query `/health` and `/ready` endpoints until status is healthy.
6. **Notify stakeholders**: send alerts via email/Slack.

## Offsite & Rotation

- Keep backups for at least **30 days**.
- Rotate storage media and verify checksums.
- Automate cleanup of expired backups via lifecycle policies.

## Notes

- Don't store secrets in backups unencrypted.
- Consider managed database services with built-in backups if you want to outsource responsibility.
