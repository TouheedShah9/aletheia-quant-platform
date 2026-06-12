#!/bin/bash
echo "ALETHEIA DEPLOY"
cp aletheia.db backups/aletheia_$(date +%Y%m%d_%H%M).db
echo "✅ Backup done"
python tests/test_suite.py && echo "✅ Tests passed" || (echo "❌ Tests failed" && exit 1)
git add . && git commit -m "Deploy: $(date)" && git push origin main
echo "✅ Deployed"