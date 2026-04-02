#!/bin/bash
set -e

echo "🚀 Setting up Jarvis for Vercel..."

# Create folder structure
mkdir -p api public

# Move files into place
[ -f chat.py ]    && mv chat.py api/chat.py       && echo "✅ api/chat.py"
[ -f index.html ] && mv index.html public/index.html && echo "✅ public/index.html"

# Set the OpenRouter API key
echo ""
read -p "🔑 Paste your OpenRouter API key: " api_key

# Install Vercel CLI if not present
if ! command -v vercel &> /dev/null; then
  echo "📦 Installing Vercel CLI..."
  npm i -g vercel
fi

# Deploy
echo ""
echo "🌐 Deploying to Vercel..."
vercel --prod -e OPENROUTER_API_KEY="$api_key"

echo ""
echo "✅ Done! Your Jarvis is live."
