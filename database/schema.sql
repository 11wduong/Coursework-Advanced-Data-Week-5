-- Create Country table
CREATE TABLE Country (
    country_id SMALLINT PRIMARY KEY IDENTITY(1,1),
    country VARCHAR(255)
);

-- Create Location table
CREATE TABLE Location (
    location_id BIGINT PRIMARY KEY IDENTITY(1,1),
    city VARCHAR(255),
    country_id SMALLINT,
    lat FLOAT,
    long FLOAT,
    FOREIGN KEY (country_id) REFERENCES Country(country_id)
);

-- Create Plant table
CREATE TABLE Plant (
    plant_id SMALLINT PRIMARY KEY IDENTITY(1,1),
    scientific_name VARCHAR(255),
    common_name VARCHAR(255),
    location_id BIGINT,
    FOREIGN KEY (location_id) REFERENCES Location(location_id)
);

-- Create Botanist table
CREATE TABLE Botanist (
    botanist_id SMALLINT PRIMARY KEY IDENTITY(1,1),
    botanist_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20)
);

-- Create Record table
CREATE TABLE Record (
    id BIGINT PRIMARY KEY IDENTITY(1,1),
    plant_id SMALLINT,
    recording_taken DATE,
    moisture FLOAT,
    temperature FLOAT,
    last_watered DATE,
    botanist_id SMALLINT,
    FOREIGN KEY (plant_id) REFERENCES Plant(plant_id),
    FOREIGN KEY (botanist_id) REFERENCES Botanist(botanist_id)
);