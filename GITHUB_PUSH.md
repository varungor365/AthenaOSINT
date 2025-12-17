# 🚀 Quick GitHub Push Guide

## Step 1: Create GitHub Repository

1. Go to: **https://github.com/new**
2. Repository name: `athena-osint` (or your preferred name)
3. Description: `AthenaOSINT - Advanced OSINT Framework with Intelligence Analysis`
4. **Make it Public or Private** (your choice)
5. **DO NOT** check any initialization options (no README, no .gitignore, no license)
6. Click **"Create repository"**

## Step 2: Push Your Code

After creating the repository, run these commands in your terminal:

```powershell
# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/athena-osint.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

**Example** (if your username is `johndoe`):
```powershell
git remote add origin https://github.com/johndoe/athena-osint.git
git branch -M main
git push -u origin main
```

GitHub will prompt for your credentials:
- **Username**: Your GitHub username
- **Password**: Use a **Personal Access Token** (not your password)

### Get Personal Access Token:
1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name: `AthenaOSINT Deploy`
4. Select scopes: ✅ **repo** (all repository permissions)
5. Click **"Generate token"**
6. **Copy the token** (you won't see it again!)
7. Use this token as your password when pushing

## Step 3: Verify Upload

After pushing, visit:
```
https://github.com/YOUR_USERNAME/athena-osint
```

You should see all your files!

---

## 🔄 Future Updates

To push updates later:
```powershell
git add .
git commit -m "Updated features"
git push
```

---

## ⚡ Ready for Droplet?

Once pushed to GitHub, follow the [DEPLOYMENT.md](DEPLOYMENT.md) guide to deploy on your DigitalOcean droplet!

**Quick Droplet Commands:**
```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Clone and deploy
git clone https://github.com/YOUR_USERNAME/athena-osint.git
cd athena-osint
chmod +x deploy.sh
./deploy.sh
```

---

**Need Help?** 
- Personal Access Token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- SSH Keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
