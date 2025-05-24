## Setup
1. Set up a PostgreSQL server with the provided Dockerfile and docker-compose.yml:
   ```bash
   docker-compose up -d
   ```    
2. Set up environment variables via a `.env` file or directly in your environment. These are expeceted to eitherin URI or key-value format:
   - `DATABASE_URL_ADMIN`
   - `DATABASE_URL_USER`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python main.py
   ```