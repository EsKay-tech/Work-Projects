/* =====================================================================
   Olist Data Warehouse — full schema
   Run order: this file creates everything in dependency order.
   Re-runnable: drops facts first, then dims (FKs are named, so drops
   are deterministic).
   ===================================================================== */

USE [data_warehouse]
GO

-- ---------------------------------------------------------------------
-- 0. Drop in reverse dependency order (facts -> dims)
-- ---------------------------------------------------------------------
IF OBJECT_ID('dbo.fact_reviews', 'U') IS NOT NULL
    DROP TABLE dbo.fact_reviews;
GO
IF OBJECT_ID('dbo.fact_order_items', 'U') IS NOT NULL
    DROP TABLE dbo.fact_order_items;
GO
IF OBJECT_ID('dbo.dim_orders', 'U') IS NOT NULL
    DROP TABLE dbo.dim_orders;
GO
IF OBJECT_ID('dbo.dim_customer', 'U') IS NOT NULL
    DROP TABLE dbo.dim_customer;
GO
IF OBJECT_ID('dbo.dim_products', 'U') IS NOT NULL
    DROP TABLE dbo.dim_products;
GO
IF OBJECT_ID('dbo.dim_sellers', 'U') IS NOT NULL
    DROP TABLE dbo.dim_sellers;
GO
IF OBJECT_ID('dbo.dim_date', 'U') IS NOT NULL
    DROP TABLE dbo.dim_date;
GO

-- ---------------------------------------------------------------------
-- 1. dim_date
--    Continuous calendar. Clustered PK on date_key serves fact joins;
--    full_date is NOT NULL and unique (one row per calendar day).
-- ---------------------------------------------------------------------
CREATE TABLE dbo.dim_date (
    [date_key]          NVARCHAR(8)  NOT NULL,
    [full_date]         DATE         NOT NULL,
    [day_of_week]       INT,
    [day_of_week_name]  NVARCHAR(255),
    [day_of_month]      INT,
    [month]             INT,
    [month_name]        NVARCHAR(255),
    [quarter]           INT,
    [fiscal_year]       INT,          -- Brazil: calendar year
    [is_weekend]        BIT,
    [is_holiday]        BIT,
    CONSTRAINT PK_dim_date PRIMARY KEY (date_key),
    CONSTRAINT UQ_dim_date_full_date UNIQUE (full_date)
)
GO

-- ---------------------------------------------------------------------
-- 2. dim_customer  (SCD Type 2)
--    Surrogate PK clustered (serves fact joins).
--    UNIQUE (customer_id, end_date): one NULL end_date allowed per
--    customer_id => exactly one current version, enforced by the engine.
--    lng needs DECIMAL(11,8): longitude spans -180..180.
-- ---------------------------------------------------------------------
CREATE TABLE dbo.dim_customer (
    [customer_key]              INT IDENTITY(1,1) NOT NULL,
    [customer_id]               NVARCHAR(255)     NOT NULL,   -- natural key
    [customer_zip_code_prefix]  NVARCHAR(255),                -- keep leading zeros
    [customer_city]             NVARCHAR(255),
    [customer_state]            NVARCHAR(255),
    [geolocation_lat]           DECIMAL(10,8),
    [geolocation_lng]           DECIMAL(11,8),
    [geolocation_city]          NVARCHAR(255),
    [geolocation_state]         NVARCHAR(255),
    [start_date]                DATE NOT NULL,
    [end_date]                  DATE NULL,
    [is_current]                BIT  NOT NULL DEFAULT 1,
    CONSTRAINT PK_dim_customer PRIMARY KEY (customer_key),
    CONSTRAINT UQ_dim_customer_id_end_date UNIQUE (customer_id, end_date)
)
GO

CREATE NONCLUSTERED INDEX IX_dim_customer_id_current
ON dbo.dim_customer (customer_id, is_current)
GO

-- ---------------------------------------------------------------------
-- 3. dim_products
--    Surrogate PK; string natural key UNIQUE.
--    Numeric lengths are INT (not NVARCHAR); measures DECIMAL(10,2)
--    (bare DECIMAL = DECIMAL(18,0) and silently truncates decimals).
--    Category name is NOT unique — many products share a category.
-- ---------------------------------------------------------------------
CREATE TABLE dbo.dim_products (
    [product_key]                    INT IDENTITY(1,1) NOT NULL,
    [product_id]                     NVARCHAR(255)     NOT NULL,  -- natural key
    [product_category_name]          NVARCHAR(255)     NULL,      -- 610 nulls in source
    [product_name_lenght]            INT,
    [product_description_lenght]     INT,
    [product_photos_qty]             INT,
    [product_weight_g]               DECIMAL(10,2),
    [product_length_cm]              DECIMAL(10,2),
    [product_height_cm]              DECIMAL(10,2),
    [product_width_cm]               DECIMAL(10,2),
    [product_category_name_english]  NVARCHAR(255),
    CONSTRAINT PK_dim_products PRIMARY KEY (product_key),
    CONSTRAINT UQ_dim_products_product_id UNIQUE (product_id)
)
GO

CREATE NONCLUSTERED INDEX IX_dim_products_product_id
ON dbo.dim_products (product_id)
GO

-- ---------------------------------------------------------------------
-- 4. dim_sellers
--    Zip prefix is NVARCHAR (leading zeros); lng DECIMAL(11,8).
-- ---------------------------------------------------------------------
CREATE TABLE dbo.dim_sellers (
    [seller_key]              INT IDENTITY(1,1) NOT NULL,
    [seller_id]               NVARCHAR(255)     NOT NULL,   -- natural key
    [seller_zip_code_prefix]  NVARCHAR(255),
    [seller_city]             NVARCHAR(255),
    [seller_state]            NVARCHAR(255),
    [geolocation_lat]         DECIMAL(10,8),
    [geolocation_lng]         DECIMAL(11,8),
    CONSTRAINT PK_dim_sellers PRIMARY KEY (seller_key),
    CONSTRAINT UQ_dim_sellers_seller_id UNIQUE (seller_id)
)
GO

CREATE NONCLUSTERED INDEX IX_dim_sellers_seller_id
ON dbo.dim_sellers (seller_id)
GO

-- ---------------------------------------------------------------------
-- 5. dim_orders
--    Clustered PK on surrogate key: serves every fact join.
--    order_purchase_timestamp is an attribute, not an access path.
-- ---------------------------------------------------------------------
CREATE TABLE dbo.dim_orders (
    [order_key]                 INT IDENTITY(1,1) NOT NULL,
    [order_id]                  NVARCHAR(255)     NOT NULL,  -- natural key
    [order_status]              NVARCHAR(255),
    [order_purchase_timestamp]  DATETIME,
    CONSTRAINT PK_dim_orders PRIMARY KEY (order_key),
    CONSTRAINT UQ_dim_orders_order_id UNIQUE (order_id)
)
GO

CREATE NONCLUSTERED INDEX IX_dim_orders_order_id
ON dbo.dim_orders (order_id)
GO

-- ---------------------------------------------------------------------
-- 6. fact_order_items
--    Grain: one row per order item.
--    PK NONCLUSTERED (surrogate is a row id, nobody filters on it);
--    the one clustered slot is spent on (date_key, product_key) for
--    date-range analytical scans.
--    UNIQUE(order_key, order_item_id): the no-double-load guardrail.
-- ---------------------------------------------------------------------
CREATE TABLE dbo.fact_order_items (
    [order_item_key]  INT IDENTITY(1,1) NOT NULL,
    [order_key]       INT               NOT NULL,
    [order_item_id]   INT               NOT NULL,
    [customer_key]    INT               NOT NULL,
    [product_key]     INT               NOT NULL,
    [seller_key]      INT               NOT NULL,
    [date_key]        NVARCHAR(8)       NOT NULL,
    [price]           DECIMAL(10,2),
    [freight_value]   DECIMAL(10,2),
    CONSTRAINT PK_fact_order_items PRIMARY KEY NONCLUSTERED (order_item_key),
    CONSTRAINT UQ_fact_order_items_order_item UNIQUE (order_key, order_item_id),
    CONSTRAINT FK_fact_order_items_order    FOREIGN KEY (order_key)    REFERENCES dbo.dim_orders   (order_key),
    CONSTRAINT FK_fact_order_items_customer FOREIGN KEY (customer_key) REFERENCES dbo.dim_customer (customer_key),
    CONSTRAINT FK_fact_order_items_product  FOREIGN KEY (product_key)  REFERENCES dbo.dim_products (product_key),
    CONSTRAINT FK_fact_order_items_seller   FOREIGN KEY (seller_key)   REFERENCES dbo.dim_sellers  (seller_key),
    CONSTRAINT FK_fact_order_items_date     FOREIGN KEY (date_key)     REFERENCES dbo.dim_date     (date_key)
)
GO

CREATE CLUSTERED INDEX CIX_fact_order_items_date
ON dbo.fact_order_items (date_key, product_key)
GO

-- ---------------------------------------------------------------------
-- 7. fact_reviews
--    Grain: one row per review. Drill-across to fact_order_items via
--    order_key (aggregate each fact to order grain first, then join).
--    Clustered on order_key alone: serves the drill-across join;
--    review_creation_date stays out of the key (earns nothing, widens
--    every secondary index).
-- ---------------------------------------------------------------------
CREATE TABLE dbo.fact_reviews (
    [review_key]              INT IDENTITY(1,1) NOT NULL,
    [review_id]               NVARCHAR(255)     NOT NULL,
    [order_key]               INT               NOT NULL,
    [review_score]            INT,
    [review_comment_message]  NVARCHAR(MAX),
    [review_creation_date]    DATETIME,
    CONSTRAINT PK_fact_reviews PRIMARY KEY NONCLUSTERED (review_key),
    CONSTRAINT UQ_fact_reviews_review_id UNIQUE (review_id),
    CONSTRAINT FK_fact_reviews_order FOREIGN KEY (order_key) REFERENCES dbo.dim_orders (order_key)
)
GO

CREATE CLUSTERED INDEX CIX_fact_reviews_order
ON dbo.fact_reviews (order_key)
GO

PRINT 'Schema created: 5 dimensions, 2 facts, named constraints throughout.'
GO
