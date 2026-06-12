#!/bin/bash
mkdir -p backups
cp aletheia.db backups/aletheia_$(date +%Y%m%d).db
ls -t backups/aletheia_*.db | tail -n +8 | xargs rm -f
echo "Backup: $(date)"