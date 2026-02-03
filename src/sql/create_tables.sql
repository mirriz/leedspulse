--Create Stations Table
CREATE TABLE stations (
    code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL -- 'Hub' or 'Spoke'
);

-- Create Routes Table
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    origin_code VARCHAR(3) REFERENCES stations(code),
    destination_code VARCHAR(3) REFERENCES stations(code),
    label VARCHAR(50),
    avg_travel_time_mins INT
);

-- Create Incidents Table (CRUD)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id INT REFERENCES routes(id),
    type VARCHAR(50) NOT NULL, -- 'Crowding', 'Delay', 'Facilities'
    severity INT CHECK (severity >= 1 AND severity <= 5),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);