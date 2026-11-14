# GitHub repository setup — RADAR-CORUÑA

GitHub repository creation is not exposed by the currently connected GitHub integration, and there is no authenticated GitHub CLI in the working environment. Therefore this folder is **prepared for publication, but is not yet uploaded to GitHub**.

1. Open https://github.com/new while signed into **neumACt**.
2. Repository name: **radar-coruna**; Visibility: **Private**.
3. Do **not** precreate README, license or .gitignore (this archive already has README and .gitignore).
4. Create repository and use the following commands in a terminal after extracting this folder:

```bash
cd radar-coruna
git init -b main
git add .
git commit -m "RADAR-CORUÑA v0.41.1 synthetic staging baseline"
git remote add origin https://github.com/neumACt/radar-coruna.git
git push -u origin main
```

Authenticate via your normal GitHub credential manager/SSH flow. Do not paste GitHub access tokens into this chat or embed them in remote URLs.

After the repository exists, the connected GitHub and Railway apps can be used to configure the deployment. The **database URI and bootstrap password** should be set in Railway Variables, never committed to source control.
