BEGIN;

CREATE TABLE public.clientes (
    "customerID" text PRIMARY KEY,
    gender text NOT NULL,
    "SeniorCitizen" smallint NOT NULL CHECK ("SeniorCitizen" IN (0, 1)),
    "Partner" text NOT NULL,
    "Dependents" text NOT NULL,
    tenure integer NOT NULL CHECK (tenure >= 0),
    "PhoneService" text NOT NULL,
    "MultipleLines" text NOT NULL,
    "InternetService" text NOT NULL,
    "OnlineSecurity" text NOT NULL,
    "OnlineBackup" text NOT NULL,
    "DeviceProtection" text NOT NULL,
    "TechSupport" text NOT NULL,
    "StreamingTV" text NOT NULL,
    "StreamingMovies" text NOT NULL,
    "Contract" text NOT NULL,
    "PaperlessBilling" text NOT NULL,
    "PaymentMethod" text NOT NULL,
    "MonthlyCharges" numeric(12, 2) NOT NULL,
    "TotalCharges" text,
    "Churn" text NOT NULL CHECK ("Churn" IN ('Yes', 'No'))
);

COPY public.clientes FROM '/docker-entrypoint-initdb.d/churn.csv'
    WITH (FORMAT csv, HEADER MATCH);

-- O CSV representa valores ausentes de TotalCharges com espaços.
ALTER TABLE public.clientes
    ALTER COLUMN "TotalCharges" TYPE numeric(12, 2)
    USING NULLIF(btrim("TotalCharges"), '')::numeric(12, 2);

COMMIT;
