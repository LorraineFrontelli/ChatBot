CREATE TABLE IF NOT EXISTS categories (
  id           SERIAL PRIMARY KEY,
  name         VARCHAR(64) NOT NULL,             
  description  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()                        
);

select * from categories

CREATE TABLE IF NOT EXISTS transaction_types (
  id      serial PRIMARY KEY,
  type    TEXT NOT NULL                                        
);

CREATE TABLE IF NOT EXISTS transactions (
  id             BIGSERIAL PRIMARY KEY,
  amount         NUMERIC(14,2) NOT NULL , 	
  type           INT REFERENCES transaction_types(id) NOT NULL DEFAULT 2,          
  category_id    INT REFERENCES categories(id) ON DELETE SET NULL,
  description    TEXT,                                                
  payment_method VARCHAR(32),                                         
  occurred_at    TIMESTAMPTZ NOT NULL,                                
  source_text    TEXT NOT NULL                                        
);

select * from transactions

-- Ãndices Ãºteis para consultas comuns
CREATE INDEX IF NOT EXISTS idx_transactions_occurred_at
  ON transactions (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_category_time
  ON transactions (category_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_localday
  ON transactions ( ((occurred_at AT TIME ZONE 'America/Sao_Paulo')::date) );

CREATE TABLE IF NOT EXISTS events (
  id           BIGSERIAL PRIMARY KEY,
  title        TEXT NOT NULL,                                          
  start_time   TIMESTAMPTZ NOT NULL,                                   
  end_time     TIMESTAMPTZ,                                            
  location     TEXT,
  notes        TEXT,
  recorded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),                     
  source_text  TEXT NOT NULL                                           
);

CREATE INDEX IF NOT EXISTS idx_events_start_time
  ON events (start_time DESC);
  
INSERT INTO transaction_types (type) VALUES
  ('INCOME'),
  ('EXPENSES'),
  ('TRANSFER');

INSERT INTO categories (name) VALUES
  ('comida'),
  ('besteira'),
  ('estudo'),
  ('fÃ©rias'),
  ('transporte'),
  ('moradia'),
  ('saÃºde'),
  ('lazer'),
  ('contas'),
  ('investimento'),
  ('presente'),
  ('outros');

-- ==============================================================================
-- Autenticação e isolamento por usuário
-- ==============================================================================
CREATE TABLE IF NOT EXISTS users (
  id           SERIAL PRIMARY KEY,
  nome         VARCHAR(100) NOT NULL,
  email        VARCHAR(150) UNIQUE NOT NULL,
  senha_hash   VARCHAR(255) NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ADD COLUMN IF NOT EXISTS em vez de recriar as tabelas: já existem
-- transactions/events com dado de teste. Sem NOT NULL de propósito — os
-- registros antigos ficam sem dono (user_id NULL) até um backfill manual;
-- travar NOT NULL agora quebraria o INSERT desses dados existentes.
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE events       ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_events_user       ON events(user_id);