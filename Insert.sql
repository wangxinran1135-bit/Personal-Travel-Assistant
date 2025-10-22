INSERT INTO users (user_id, name, email, password_hash, user_role, phone) VALUES
  (1, 'Alice', 'alice@example.com', 'hash1', 'Tourist', '+61-400-000001'),
  (2, 'Bob',   'bob@example.com',   'hash2', 'Tourist', '+61-400-000002'),
  (3, 'Carol', 'carol@example.com', 'hash3', 'Tourist', '+61-400-000003'),
  (4, 'OceanTours', 'ocean@example.com', 'hash4', 'ServiceProvider', '+61-400-100001'),
  (5, 'CityEats',   'city@example.com',  'hash5', 'ServiceProvider', '+61-400-100002'),
  (6, 'HarborHotel','harbor@example.com','hash6', 'ServiceProvider', '+61-400-100003'),
  (7, 'Admin', 'admin@example.com', 'hashadmin', 'TechnicalAdmin', NULL);

INSERT INTO profiles (user_id, preferred_language, timezone, address) VALUES
  (1, 'en-AU', 'Australia/Sydney', 'Sydney, NSW, Australia'),
  (2, 'en-AU', 'Australia/Sydney', 'Manly, NSW, Australia'),
  (3, 'zh-CN', 'Asia/Shanghai', '上海市, 中国');

INSERT INTO preferences (user_id, interests, constraints, travel_pace, travel_style) VALUES
  (1, '["museum","food","hiking"]'::jsonb, '{"diet":"vegetarian","accessibility":false}'::jsonb, 'Normal', 'Comfort'),
  (2, '["beach","food"]'::jsonb, '{"diet":"none"}'::jsonb, 'Slow', 'Economy'),
  (3, '["shopping","theatre"]'::jsonb, '{"time":"evenings"}'::jsonb, 'Fast', 'Premium');

INSERT INTO service_providers (provider_id, user_id, name, category, description, location, contact_info) VALUES
  (1, 4, 'Ocean Tours', 'Tour', 'Boat tours around Sydney Harbour', 'Circular Quay, Sydney', '+61-2-9000-1000'),
  (2, 5, 'City Eats',   'Restaurant', 'Popular city food tours and dining experiences', 'CBD Sydney', 'info@cityeats.example'),
  (3, 6, 'Harbor Hotel','Hotel', 'Comfortable stay near the harbor', 'The Rocks, Sydney', 'reservations@harbor.example');

INSERT INTO service_offerings (offering_id, provider_id, title, description, category, status) VALUES
  (1, 1, 'Harbour Sunset Cruise', 'Evening cruise around the harbour', 'Tour', 'Active'),
  (2, 1, 'Whale Watching', 'Seasonal whale watching tour', 'Tour', 'Active'),
  (3, 2, 'Gourmet Food Walk', '3-hour guided food walk', 'Food', 'Active'),
  (4, 2, 'Cooking Class', 'Hands-on cooking experience', 'Food', 'Draft'),
  (5, 3, 'Harbor View Deluxe Room', 'Deluxe room with harbor view', 'Lodging', 'Active');

INSERT INTO inventories (inventory_id, offering_id, date, time_slot, capacity, available, status) VALUES
  (1, 1, '2025-11-01', '18:00-20:00', 50, 45, 'Open'),
  (2, 1, '2025-11-02', '18:00-20:00', 50, 50, 'Open'),
  (3, 2, '2025-11-05', '07:00-12:00', 30, 10, 'Open'),
  (4, 3, '2025-10-25', '11:00-14:00', 20, 5, 'Open'),
  (5, 4, '2025-12-01', '15:00-17:00', 12, 12, 'Open'),
  (6, 5, '2025-11-01', '14:00-16:00', 10, 2, 'Open');

INSERT INTO places (place_id, name, category, description, address, opening_hours) VALUES
  (1, 'Sydney Opera House', 'Attraction', 'Iconic performing arts venue', 'Bennelong Point, Sydney', '09:00-17:00'),
  (2, 'Royal Botanic Garden', 'Attraction', 'Large public garden', 'Mrs Macquaries Rd, Sydney', '06:00-18:00'),
  (3, 'Circular Quay Food Market', 'Food', 'Street food and stalls', 'Circular Quay, Sydney', '10:00-20:00'),
  (4, 'Sydney Harbour Bridge', 'Attraction', 'Historic steel through arch bridge', 'Bridge St, Sydney', '24/7');

INSERT INTO itineraries (itinerary_id, user_id, title, description, status, start_date, end_date) VALUES
  (1, 1, 'Sydney Weekend', 'Weekend in Sydney', 'Planned', '2025-11-01', '2025-11-03'),
  (2, 2, 'Beach Holiday', 'Relaxing beach trip', 'Confirmed', '2025-12-15', '2025-12-20'),
  (3, 3, 'Food & Culture', 'Explore city food and theatre', 'Planned', '2025-10-24', '2025-10-26');

INSERT INTO budgets (budget_id, itinerary_id, daily_limit, total_limit) VALUES
  (1, 1, 200.00, 600.00),
  (2, 2, 150.00, 900.00),
  (3, 3, 250.00, 750.00);

INSERT INTO itinerary_days (day_id, itinerary_id, date, day_number) VALUES
  (1, 1, '2025-11-01', 1),
  (2, 1, '2025-11-02', 2),
  (3, 2, '2025-12-15', 1),
  (4, 3, '2025-10-24', 1),
  (5, 3, '2025-10-25', 2);

INSERT INTO activities (activity_id, day_id, type, start_time, end_time, place_id, mode, estimated_duration, notes) VALUES
  (1, 1, 'VisitPOI', '2025-11-01 09:00:00+11', '2025-11-01 11:00:00+11', 1, NULL, NULL, 'Visit Opera House'),
  (2, 1, 'Meal',     '2025-11-01 12:00:00+11', '2025-11-01 13:00:00+11', 3, NULL, NULL, 'Lunch at Circular Quay'),
  (3, 1, 'VisitPOI', '2025-11-01 18:00:00+11', '2025-11-01 20:00:00+11', NULL, NULL, NULL, 'Harbour sunset cruise'),
  (4, 2, 'TransportLeg','2025-11-02 08:00:00+11', '2025-11-02 09:00:00+11', NULL, 'Bus', '01:00:00', 'Transfer to airport'),
  (5, 3, 'VisitPOI', '2025-12-15 10:00:00+11', '2025-12-15 12:00:00+11', 2, NULL, NULL, 'Botanic Garden visit'),
  (6, 4, 'Meal',     '2025-10-24 19:00:00+11', '2025-10-24 21:00:00+11', 3, NULL, NULL, 'Dinner and theatre');

INSERT INTO bookings (booking_id, activity_id, provider_id, status, price, confirmation_code) VALUES
  (1, 3, 1, 'Confirmed', 120.00, 'CRUISE123'),
  (2, 2, 2, 'Confirmed', 45.00,  'LUNCH456'),
  (3, NULL, 3, 'Pending', 320.00, 'ROOM789');  -- booking not tied to a specific activity

INSERT INTO calendar_events (event_id, booking_id, external_id, title, start_time, end_time, sync_status, last_synced) VALUES
  (1, 1, 'gcal_1', 'Sunset Cruise', '2025-11-01 18:00:00+11', '2025-11-01 20:00:00+11', 'Synced', '2025-10-18 10:00:00+11'),
  (2, 2, 'gcal_2', 'Gourmet Lunch', '2025-11-01 12:00:00+11', '2025-11-01 13:00:00+11', 'Synced', '2025-10-18 10:05:00+11'),
  (3, 3, 'gcal_3', 'Hotel Reservation', '2025-11-01 14:00:00+11', '2025-11-03 11:00:00+11', 'Pending', NULL);

INSERT INTO expenses (expense_id, itinerary_id, day_id, amount, expense_type, description, date) VALUES
  (1, 1, 1,  45.00,  'Transport', 'Uber from airport', '2025-11-01'),
  (2, 1, 1, 120.00,  'Activity',  'Harbour cruise (prepaid)', '2025-11-01'),
  (3, 2, 3,  80.00,  'Meal', 'Group dinner', '2025-12-15'),
  (4, 3, 4,  60.00,  'Entertainment', 'Theatre tickets', '2025-10-24');

SELECT setval(pg_get_serial_sequence('users','user_id'), COALESCE(MAX(user_id),0)) FROM users;
SELECT setval(pg_get_serial_sequence('service_providers','provider_id'), COALESCE(MAX(provider_id),0)) FROM service_providers;
SELECT setval(pg_get_serial_sequence('service_offerings','offering_id'), COALESCE(MAX(offering_id),0)) FROM service_offerings;
SELECT setval(pg_get_serial_sequence('inventories','inventory_id'), COALESCE(MAX(inventory_id),0)) FROM inventories;
SELECT setval(pg_get_serial_sequence('places','place_id'), COALESCE(MAX(place_id),0)) FROM places;
SELECT setval(pg_get_serial_sequence('itineraries','itinerary_id'), COALESCE(MAX(itinerary_id),0)) FROM itineraries;
SELECT setval(pg_get_serial_sequence('budgets','budget_id'), COALESCE(MAX(budget_id),0)) FROM budgets;
SELECT setval(pg_get_serial_sequence('itinerary_days','day_id'), COALESCE(MAX(day_id),0)) FROM itinerary_days;
SELECT setval(pg_get_serial_sequence('activities','activity_id'), COALESCE(MAX(activity_id),0)) FROM activities;
SELECT setval(pg_get_serial_sequence('bookings','booking_id'), COALESCE(MAX(booking_id),0)) FROM bookings;
SELECT setval(pg_get_serial_sequence('calendar_events','event_id'), COALESCE(MAX(event_id),0)) FROM calendar_events;
SELECT setval(pg_get_serial_sequence('expenses','expense_id'), COALESCE(MAX(expense_id),0)) FROM expenses;
