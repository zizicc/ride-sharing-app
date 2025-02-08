# Usage

### Allow Cross-Origin CSRF Requests

If your Django backend and frontend run on different domains 
(e.g., frontend at `https://yourfrontend.com` and backend at `https://yourapi.com`), 
Django may block cross-origin requests due to CSRF protection. 
To resolve this issue, you need to configure `CSRF_TRUSTED_ORIGINS` in `settings.py` to include the frontend domain:

```python
# settings.py
CSRF_TRUSTED_ORIGINS = ['https://yourfrontend.com:8000']

### Updating Gmail API Token Using Python 3

To refresh your Gmail API token, cd to .../web-app folder, then run

  ```sh
  python3 gmail_service.py
