-- ============================================================
--  AutoJobApply — MySQL Schema
--  Run this in MySQL Workbench to set up the database
-- ============================================================

CREATE DATABASE IF NOT EXISTS autojobapply
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE autojobapply;

-- ------------------------------------------------------------
-- 1. USERS — core authentication table
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  full_name        VARCHAR(150)  NOT NULL,
  email            VARCHAR(200)  NOT NULL UNIQUE,
  password_hash    VARCHAR(255)  NOT NULL,
  phone            VARCHAR(20)   DEFAULT NULL,
  location         VARCHAR(150)  DEFAULT NULL,
  profile_photo    VARCHAR(500)  DEFAULT NULL,
  theme_pref       ENUM('light','dark') DEFAULT 'dark',
  is_verified      TINYINT(1)    DEFAULT 0,
  reset_token      VARCHAR(255)  DEFAULT NULL,
  reset_expires    DATETIME      DEFAULT NULL,
  created_at       DATETIME      DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. USER PROFILES — professional details
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profiles (
  id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id             INT UNSIGNED NOT NULL UNIQUE,
  headline            VARCHAR(255)  DEFAULT NULL,
  summary             TEXT          DEFAULT NULL,
  linkedin_url        VARCHAR(500)  DEFAULT NULL,
  github_url          VARCHAR(500)  DEFAULT NULL,
  portfolio_url       VARCHAR(500)  DEFAULT NULL,
  resume_url          VARCHAR(500)  DEFAULT NULL,
  resume_text         LONGTEXT      DEFAULT NULL,
  skills              JSON          DEFAULT NULL,
  experience_years    DECIMAL(4,1)  DEFAULT 0,
  current_salary      DECIMAL(12,2) DEFAULT NULL,
  expected_salary     DECIMAL(12,2) DEFAULT NULL,
  work_history        JSON          DEFAULT NULL,
  education           JSON          DEFAULT NULL,
  certifications      JSON          DEFAULT NULL,
  languages           JSON          DEFAULT NULL,
  job_type_pref       SET('full-time','part-time','contract','internship','remote') DEFAULT 'full-time',
  willing_to_relocate TINYINT(1)    DEFAULT 0,
  notice_period_days  INT           DEFAULT 0,
  custom_answers      JSON          DEFAULT NULL,
  created_at          DATETIME      DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. JOB LISTINGS — fetched / pasted jobs
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_listings (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         INT UNSIGNED NOT NULL,
  title           VARCHAR(255)  NOT NULL,
  company         VARCHAR(255)  DEFAULT NULL,
  location        VARCHAR(255)  DEFAULT NULL,
  job_url         VARCHAR(1000) NOT NULL,
  source          VARCHAR(100)  DEFAULT 'manual',
  description     LONGTEXT      DEFAULT NULL,
  salary_range    VARCHAR(100)  DEFAULT NULL,
  job_type        VARCHAR(50)   DEFAULT NULL,
  is_remote       TINYINT(1)    DEFAULT 0,
  requirements    JSON          DEFAULT NULL,
  status          ENUM('pending','saved','applied','rejected','ignored') DEFAULT 'pending',
  fetched_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
  created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. APPLICATIONS — actual application attempts
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id           INT UNSIGNED NOT NULL,
  job_id            INT UNSIGNED NOT NULL,
  form_data         JSON          DEFAULT NULL,
  custom_qa         JSON          DEFAULT NULL,
  cover_letter      TEXT          DEFAULT NULL,
  status            ENUM('draft','review','submitting','submitted','failed') DEFAULT 'draft',
  review_notes      TEXT          DEFAULT NULL,
  screenshot_url    VARCHAR(500)  DEFAULT NULL,
  error_message     TEXT          DEFAULT NULL,
  submitted_at      DATETIME      DEFAULT NULL,
  created_at        DATETIME      DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (job_id)  REFERENCES job_listings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 5. AUTOMATION SESSIONS — log of each Playwright run
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS automation_sessions (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id          INT UNSIGNED NOT NULL,
  application_id   INT UNSIGNED NOT NULL,
  session_log      JSON    DEFAULT NULL,
  steps_completed  INT     DEFAULT 0,
  steps_total      INT     DEFAULT 0,
  started_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at     DATETIME DEFAULT NULL,
  error_message    TEXT    DEFAULT NULL,
  FOREIGN KEY (user_id)         REFERENCES users(id)        ON DELETE CASCADE,
  FOREIGN KEY (application_id)  REFERENCES applications(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Indexes for performance
-- ------------------------------------------------------------
CREATE INDEX idx_jobs_user     ON job_listings(user_id, status);
CREATE INDEX idx_apps_user     ON applications(user_id, status);
CREATE INDEX idx_apps_job      ON applications(job_id);
CREATE INDEX idx_sessions_app  ON automation_sessions(application_id);

-- ------------------------------------------------------------
-- Sample verification query
-- ------------------------------------------------------------
-- SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.TABLES
-- WHERE TABLE_SCHEMA = 'autojobapply';
