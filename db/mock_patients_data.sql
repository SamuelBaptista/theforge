CREATE TABLE IF NOT EXISTS patient (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    dob TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

INSERT INTO patient (first_name, last_name, dob, address, phone, email) VALUES
    ('Samuel', '', '1985-03-22', '456 Oak St, Medville, ST 12345', '(555) 234-5678', 's.johnson@email.com'),
    ('Emma', '', '1990-06-15', '789 Pine St, Greenville, ST 54321', '(555) 876-5432', 'emma.smith@email.com'),
    ('Felipe', '', '1982-12-10', '321 Elm St, Springfield, ST 67890', '(555) 345-6789', 'michael.brown@email.com'),
    ('Sophia', 'Davis', '1995-07-07', '987 Maple St, Riverdale, ST 56789', '(555) 234-0987', 'sophia.davis@email.com'),
    ('James', 'Wilson', '1988-09-25', '654 Cedar St, Lakeside, ST 34567', '(555) 765-4321', 'james.wilson@email.com'),
    ('Olivia', 'Martinez', '1993-04-18', '159 Birch St, Hilltown, ST 23456', '(555) 876-2345', 'olivia.martinez@email.com'),
    ('William', 'Anderson', '1981-11-30', '753 Chestnut St, Beachside, ST 67812', '(555) 234-7654', 'william.anderson@email.com'),
    ('Ava', 'Garcia', '1992-08-20', '852 Willow St, Mountainview, ST 45678', '(555) 908-7654', 'ava.garcia@email.com'),
    ('Benjamin', 'Hernandez', '1987-05-14', '951 Redwood St, Sunset, ST 78945', '(555) 567-8901', 'benjamin.hernandez@email.com'),
    ('Charlotte', 'Lopez', '1998-02-10', '159 Cypress St, Meadowbrook, ST 67834', '(555) 321-5678', 'charlotte.lopez@email.com')
ON CONFLICT(email) DO NOTHING;
