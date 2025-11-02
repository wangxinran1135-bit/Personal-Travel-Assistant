CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  user_role VARCHAR(50) NOT NULL
    CHECK (user_role IN ('Tourist', 'ServiceProvider', 'TechnicalAdmin')),
  phone VARCHAR(50),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
  user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  preferred_language VARCHAR(50),
  timezone VARCHAR(100),
  address TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE preferences (
  user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  interests JSONB NOT NULL DEFAULT '{}'::jsonb,
  constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
  travel_pace VARCHAR(50),
  travel_style VARCHAR(50)
    CHECK (travel_style IN ('Economy', 'Comfort', 'Premium', 'Luxury')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_providers (
  provider_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  description TEXT,
  location TEXT,
  contact_info TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_offerings (
  offering_id SERIAL PRIMARY KEY,
  provider_id INT NOT NULL REFERENCES service_providers(provider_id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100),
  status VARCHAR(20)
    CHECK (status IN ('Active', 'Inactive', 'Draft', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventories (
  inventory_id SERIAL PRIMARY KEY,
  offering_id INT NOT NULL REFERENCES service_offerings(offering_id) ON DELETE CASCADE,
  date DATE NOT NULL,
  time_slot VARCHAR(50),
  capacity INT NOT NULL DEFAULT 0,
  available INT NOT NULL DEFAULT 0,
  status VARCHAR(20)
    CHECK (status IN ('Open', 'SoldOut', 'Closed')),
  last_updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (offering_id, date, time_slot)
);

CREATE TABLE places (
  place_id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  description TEXT,
  address TEXT,
  opening_hours TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itineraries (
  itinerary_id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(20)
    CHECK (status IN ('Planned', 'Confirmed', 'Completed')),
  start_date DATE,
  end_date DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE budgets (
  budget_id SERIAL PRIMARY KEY,
  itinerary_id INT NOT NULL UNIQUE REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
  daily_limit NUMERIC(12,2),
  total_limit NUMERIC(12,2),
  last_updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itinerary_days (
  day_id SERIAL PRIMARY KEY,
  itinerary_id INT NOT NULL REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
  date DATE NOT NULL,
  day_number INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (itinerary_id, date)
);

CREATE TABLE activities (
  activity_id SERIAL PRIMARY KEY,
  day_id INT NOT NULL REFERENCES itinerary_days(day_id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL
    CHECK (type IN ('VisitPOI', 'Meal', 'TransportLeg')),
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  place_id INT REFERENCES places(place_id) ON DELETE SET NULL,
  mode VARCHAR(100),
  estimated_duration INTERVAL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
  booking_id SERIAL PRIMARY KEY,
  activity_id INT UNIQUE REFERENCES activities(activity_id) ON DELETE SET NULL,
  provider_id INT NOT NULL REFERENCES service_providers(provider_id) ON DELETE RESTRICT,
  status VARCHAR(20)
    CHECK (status IN ('Pending', 'Confirmed', 'Cancelled')),
  price NUMERIC(12,2),
  confirmation_code VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE calendar_events (
  event_id SERIAL PRIMARY KEY,
  booking_id INT NOT NULL UNIQUE REFERENCES bookings(booking_id) ON DELETE CASCADE,
  external_id VARCHAR(255),
  title VARCHAR(255),
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  sync_status VARCHAR(20)
    CHECK (sync_status IN ('Pending', 'Synced', 'Failed')),
  last_synced TIMESTAMPTZ
);

CREATE TABLE expenses (
  expense_id SERIAL PRIMARY KEY,
  itinerary_id INT NOT NULL REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
  day_id INT REFERENCES itinerary_days(day_id) ON DELETE SET NULL,
  amount NUMERIC(12,2),
  expense_type VARCHAR(100),
  description TEXT,
  date DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS system_logs (
    log_id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    user_id INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);


CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
