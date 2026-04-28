#!/bin/bash
# ══════════════════════════════════════════
#   SuperBot — GitHub ga push qilish
#   Bir marta ishlatiladi
# ══════════════════════════════════════════

echo ""
echo "🚀 SuperBot — GitHub Setup"
echo "══════════════════════════"
echo ""

# GitHub ma'lumotlar
read -p "GitHub username: " GH_USER
read -p "Repository nomi (default: superbot): " REPO_NAME
REPO_NAME=${REPO_NAME:-superbot}
read -s -p "GitHub Personal Access Token (ghp_...): " GH_TOKEN
echo ""

REPO_URL="https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${REPO_NAME}.git"

echo ""
echo "📁 Git repo yaratilmoqda..."
git init
git add .
git commit -m "🚀 Initial commit: SuperBot"

echo ""
echo "☁️ GitHub da repo yaratilmoqda..."
curl -s -X POST \
  -H "Authorization: token ${GH_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"${REPO_NAME}\",\"private\":true,\"description\":\"Shaxsiy Telegram Super Bot\"}" \
  > /dev/null

sleep 2

echo "📤 Push qilinmoqda..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
git branch -M main
git push -u origin main

echo ""
echo "✅ Muvaffaqiyat!"
echo "🔗 Repo: https://github.com/${GH_USER}/${REPO_NAME}"
echo ""
echo "Keyingi qadam: Railway ga ulang"
echo "→ https://railway.app → New Project → GitHub → ${REPO_NAME}"
