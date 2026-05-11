-- Sandbox Aadhaar seed (10 temporary records)
-- Target table: aadhaar_aadhaardatabase
-- Safe to run multiple times (upsert).

INSERT INTO aadhaar_aadhaardatabase (
    aadhaar_number,
    first_name,
    middle_name,
    last_name,
    full_name,
    date_of_birth,
    address,
    gender,
    phone_number,
    created_at
)
VALUES
    ('900000000005', 'Aarav',  '', 'Mehta',  'Aarav Mehta',   '1996-04-14', '12 MG Road, Indiranagar, Bengaluru, Karnataka - 560038', 'M', '9876500005', NOW()),
    ('900000000006', 'Diya',   '', 'Sharma', 'Diya Sharma',   '1998-09-03', '44 Sector 15, Noida, Uttar Pradesh - 201301',             'F', '9876500006', NOW()),
    ('900000000007', 'Rohan',  '', 'Patel',  'Rohan Patel',   '1994-01-27', '18 Navrangpura, Ahmedabad, Gujarat - 380009',             'M', '9876500007', NOW()),
    ('900000000008', 'Ishita', '', 'Nair',   'Ishita Nair',   '1997-06-18', '205 Marine Drive, Kochi, Kerala - 682031',                'F', '9876500008', NOW()),
    ('900000000009', 'Karan',  '', 'Singh',  'Karan Singh',   '1993-11-09', '90 Model Town, Ludhiana, Punjab - 141002',                'M', '9876500009', NOW()),
    ('900000000010', 'Ananya', '', 'Reddy',  'Ananya Reddy',  '1999-02-22', '8 Banjara Hills, Hyderabad, Telangana - 500034',          'F', '9876500010', NOW()),
    ('900000000011', 'Vivaan', '', 'Joshi',  'Vivaan Joshi',  '1995-07-05', '55 Shivaji Nagar, Pune, Maharashtra - 411005',            'M', '9876500011', NOW()),
    ('900000000012', 'Meera',  '', 'Kapoor', 'Meera Kapoor',  '1996-12-16', '71 Rajouri Garden, New Delhi, Delhi - 110027',            'F', '9876500012', NOW()),
    ('900000000013', 'Aditya', '', 'Verma',  'Aditya Verma',  '1992-03-30', '23 Gomti Nagar, Lucknow, Uttar Pradesh - 226010',         'M', '9876500013', NOW()),
    ('900000000014', 'Kavya',  '', 'Iyer',   'Kavya Iyer',    '1998-10-12', '39 T Nagar, Chennai, Tamil Nadu - 600017',                'F', '9876500014', NOW())
ON CONFLICT (aadhaar_number) DO UPDATE
SET
    first_name = EXCLUDED.first_name,
    middle_name = EXCLUDED.middle_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    date_of_birth = EXCLUDED.date_of_birth,
    address = EXCLUDED.address,
    gender = EXCLUDED.gender,
    phone_number = EXCLUDED.phone_number;
