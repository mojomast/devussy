# Devussy VPS Deployment Workflow

This guide outlines the standard process for moving features from your local development environment to the production VPS.

## 🔄 The Cycle: Local → Git → VPS

### Phase 1: Local Development & Testing
1.  Make your code changes in VS Code.
2.  Test locally if possible (using `npm run dev` or the local docker compose).
3.  **Verify Python Syntax** (Crucial for backend changes):
    ```powershell
    python -m py_compile devussy-web/streaming_server/app.py
    ```

### Phase 2: Push to Repository
Once your changes are ready, push them to the `devussy-testing` branch.

1.  **Stage and Commit**:
    ```powershell
    git add .
    git commit -m "Description of your changes"
    ```
2.  **Push to GitHub**:
    ```powershell
    git push origin devussy-testing
    ```

---

### Phase 3: Deploy on VPS
Connect to your VPS and update the running application.

1.  **SSH into VPS**:
    ```bash
    ssh user@your-vps-ip
    ```

2.  **Navigate to Project Directory**:
    ```bash
    cd ~/devussy/devussy-web
    ```

3.  **Pull Latest Changes**:
    ```bash
    git pull origin devussy-testing
    ```

4.  **Rebuild and Restart Containers**:
    *You must use `--build` to ensure Python code changes are baked into the new image.*
    ```bash
    docker compose -f docker-compose.prod.yml up -d --build
    ```

5.  **Verify Deployment**:
    Check the logs to ensure the server started correctly.
    ```bash
    docker compose -f docker-compose.prod.yml logs -f streaming-server
    ```

---

## ⚡ Quick Command Reference

**On Local Machine:**
```powershell
git add .
git commit -m "Update feature"
git push origin devussy-testing
```

**On VPS:**
```bash
cd ~/devussy/devussy-web
git pull origin devussy-testing
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 🔑 Environment Variables (First Time / Changes Only)
If you added new environment variables (like `REQUESTY_API_KEY`), you must update the `.env` file on the VPS before rebuilding.

1.  Edit `.env`:
    ```bash
    nano .env
    ```
2.  Add/Update variables:
    ```
    REQUESTY_API_KEY=sk-xxxx
    STREAMING_SECRET=your_secret
    ```
3.  Save (`Ctrl+O`, `Enter`) and Exit (`Ctrl+X`).
4.  Run the rebuild command (Step 4 above).

## 🛠 Troubleshooting
If things break after deployment, see `DEPLOYMENT_NOTES.md` for detailed debugging steps.
