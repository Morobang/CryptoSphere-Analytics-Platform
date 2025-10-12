-- =====================================================
-- 1. DATABASE SETUP
-- =====================================================

-- Use master to create database
USE master;
GO

-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'cryptosphere_analytics')
BEGIN
    CREATE DATABASE cryptosphere_analytics;
    PRINT 'Database [cryptosphere_analytics] created successfully';
END
ELSE
BEGIN
    PRINT 'Database [cryptosphere_analytics] already exists';
END
GO

-- Switch to our database
USE cryptosphere_analytics;
GO

-- =====================================================
-- 2. CREATE SCHEMAS (MEDALLION LAYERS)
-- =====================================================

-- Bronze Layer Schema (Raw Data)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'bronze')
BEGIN
    EXEC('CREATE SCHEMA bronze');
    PRINT 'Schema [bronze] created successfully';
END
ELSE
BEGIN
    PRINT 'Schema [bronze] already exists';
END
GO

-- Silver Layer Schema (Clean Data)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'silver')
BEGIN
    EXEC('CREATE SCHEMA silver');
    PRINT 'Schema [silver] created successfully';
END
ELSE
BEGIN
    PRINT 'Schema [silver] already exists';
END
GO

-- Gold Layer Schema (Analytics Data)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold')
BEGIN
    EXEC('CREATE SCHEMA gold');
    PRINT 'Schema [gold] created successfully';
END
ELSE
BEGIN
    PRINT 'Schema [gold] already exists';
END
GO
