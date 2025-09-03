CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';


CREATE SCHEMA IF NOT EXISTS kopi_chat;

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON SCHEMA kopi_chat TO kopi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA kopi_chat TO kopi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA kopi_chat TO kopi_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA kopi_chat GRANT ALL ON TABLES TO kopi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA kopi_chat GRANT ALL ON SEQUENCES TO kopi_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully for Kopi Chat Application';
END $$;
