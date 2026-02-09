-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Incidents table
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Links report to a specific User
    owner_id UUID NOT NULL,
    
    -- Service ID from Rail API
    train_id VARCHAR(50), 
    
    -- Report Details
    type VARCHAR(50) NOT NULL, -- e.g., "Crowding"
    severity INTEGER NOT NULL, -- 1 to 5
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT fk_user
      FOREIGN KEY(owner_id) 
      REFERENCES users(id)
      ON DELETE CASCADE
);