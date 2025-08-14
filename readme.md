# Comput3 AI ComfyUI Setup Python Script

**Copyright © 2025 [Daïm Al-Yad (@daimalyad)](https://x.com/daimalyad)**  
Licensed under the [MIT License](LICENSE)

This script automates launching a Comput3 ComfyUI workload and installing your desired nodes and models—both whitelisted and non-whitelisted—while handling reboot cycles and installation order for you.

---

## 📋 Usage Instructions

### 1. Get Your API Key
- Log in to your [Comput3 AI Dashboard](https://launch.comput3.ai/).
- Copy your Comput3 API key (it usually begins with `c3_api_...`).
- Paste it into the `COMPUT3_API_KEY` variable in the script.

### 2. Choose Workload Type and Duration
- **`WORKLOAD_TYPE`**: Leave as `"media:fast"` (the only available type as of August 2025).
- **`WORKLOAD_HOURS`**: Set how many hours your Comput3 ComfyUI node will run before auto-termination.

### 3. Add Whitelisted Nodes
- Edit the `NODE_QUERIES` list to include the nodes you want from Comput3's **whitelisted** catalog.
- You can use:
  - Full names copied from the whitelist.
  - Partial names or repo titles — the script matches them leniently.

### 4. Add Whitelisted Models
- Edit the `WHITELISTED_MODEL_QUERIES` list to include models from the **whitelisted** catalog.
- You can specify:
  - Display names from the whitelist.
  - Filenames.
  - Partial matches of either.

### 5. Add Custom GitHub Nodes *(Optional)*
- Add full GitHub repository URLs to `GITHUB_NODE_URLS`.
- **Note:** The script *always* installs [`apeirography/daimalyadnodes`](https://github.com/apeirography/daimalyadnodes) automatically to enable non-whitelisted model installs.

### 6. Add Non-Whitelisted Models *(Optional)*
Add entries to `NON_WHITELISTED_MODELS` as dictionaries with:
```python
{
    "url": "DIRECT_DOWNLOAD_URL",
    "filename": "MODEL_FILENAME",
    "subfolder": "diffusion_models",  # or loras, controlnet, etc.
    "sha256": ""  # optional checksum
}
markdown
# Comput3 AI ComfyUI Setup Python Script

**Copyright © 2025 [Daïm Al-Yad (@daimalyad)](https://github.com/daimalyad)**  
Licensed under the [MIT License](LICENSE)

This script automates launching a Comput3 ComfyUI workload and installing your desired nodes and models—both whitelisted and non-whitelisted—while handling reboot cycles and installation order for you.

---

## 📋 Usage Instructions

### 1. Get Your API Key
- Log in to your [Comput3 Dashboard](https://comput3.ai/).
- Copy your Comput3 API key (it usually begins with `c3_api_...`).
- Paste it into the `COMPUT3_API_KEY` variable in the script.

### 2. Choose Workload Type and Duration
- **`WORKLOAD_TYPE`**: Leave as `"media:fast"` (the only available type as of August 2025).
- **`WORKLOAD_HOURS`**: Set how many hours your Comput3 ComfyUI node will run before auto-termination.

### 3. Add Whitelisted Nodes
- Edit the `NODE_QUERIES` list to include the nodes you want from Comput3's **whitelisted** catalog.
- You can use:
  - Full names copied from the whitelist.
  - Partial names or repo titles — the script matches them leniently.

### 4. Add Whitelisted Models
- Edit the `WHITELISTED_MODEL_QUERIES` list to include models from the **whitelisted** catalog.
- You can specify:
  - Display names from the whitelist.
  - Filenames.
  - Partial matches of either.

### 5. Add Custom GitHub Nodes *(Optional)*
- Add full GitHub repository URLs to `GITHUB_NODE_URLS`.
- **Note:** The script *always* installs [`apeirography/daimalyadnodes`](https://github.com/apeirography/daimalyadnodes) automatically to enable non-whitelisted model installs.

### 6. Add Non-Whitelisted Models *(Optional)*
Add entries to `NON_WHITELISTED_MODELS` as dictionaries with:
```python
{
    "url": "DIRECT_DOWNLOAD_URL",
    "filename": "MODEL_FILENAME",
    "subfolder": "diffusion_models",  # or loras, controlnet, etc.
    "sha256": ""  # optional checksum
}
````

* **`url`**: Direct download link to the model file.
* **`filename`**: Exact filename to save on the server.
* **`subfolder`**: Target directory inside `/models/`.
* **`sha256`** *(optional)*: File integrity check.

### 7. Run the Script

* Save your changes to the `.py` file.
* Run from your terminal:

```bash
python comput3_custom_comfyui_setup.py
```

* The script will:

  1. Launch your Comput3 ComfyUI workload.
  2. Install whitelisted nodes and models.
  3. Install your custom GitHub nodes.
  4. Reboot ComfyUI and wait for it to fully restart.
  5. Install non-whitelisted models.

### 8. Start using ComfyUI

* Return to your [Comput3 AI Dashboard](https://launch.comput3.ai/) dashboard and go into ComfyUI to use your fully setup instance.

Cheers!