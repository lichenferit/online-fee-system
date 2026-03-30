CREATE DATABASE IF NOT EXISTS feesystem;
USE feesystem;

CREATE TABLE feeapp_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME NULL,
    is_superuser TINYINT(1) NOT NULL,
    username VARCHAR(150) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    is_staff TINYINT(1) NOT NULL,
    is_active TINYINT(1) NOT NULL,
    date_joined DATETIME NOT NULL
);

CREATE TABLE feeapp_clerk (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clerk_id VARCHAR(20) NOT NULL UNIQUE,
    clerk_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NULL,
    position VARCHAR(50) NULL,
    cnic VARCHAR(15) NULL,
    gender VARCHAR(10) NULL,
    user_id INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES feeapp_user(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    heading VARCHAR(255) NOT NULL,
    short_description LONGTEXT NOT NULL,
    image VARCHAR(250) NULL DEFAULT NULL,
    created_at DATETIME NOT NULL,
    user_id_id INT NOT NULL,
    FOREIGN KEY (user_id_id) REFERENCES feeapp_user(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_coursegroup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_description LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    program_id_id INT NOT NULL,
    user_id_id INT NOT NULL,
    FOREIGN KEY (program_id_id) REFERENCES feeapp_programs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id_id) REFERENCES feeapp_user(id) ON DELETE CASCADE
);

CREATE TABLE django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data LONGTEXT NOT NULL,
    expire_date DATETIME(6) NOT NULL,
    INDEX django_session_expire_date_a5c62663 (expire_date)
);

CREATE TABLE feeapp_session (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year VARCHAR(20) NOT NULL DEFAULT '2024'
);

CREATE TABLE feeapp_province (
    id INT AUTO_INCREMENT PRIMARY KEY,
    province VARCHAR(200) NOT NULL
);

CREATE TABLE feeapp_district (
    id INT AUTO_INCREMENT PRIMARY KEY,
    district VARCHAR(200) NOT NULL
);

CREATE TABLE feeapp_schemeofstudy (
    id INT AUTO_INCREMENT PRIMARY KEY,
    program_id INT NOT NULL,
    course_group_id INT NOT NULL,
    session_id INT NOT NULL,
    FOREIGN KEY (program_id) REFERENCES feeapp_programs(id) ON DELETE CASCADE,
    FOREIGN KEY (course_group_id) REFERENCES feeapp_coursegroup(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES feeapp_session(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_schemecourse (
    id INT AUTO_INCREMENT PRIMARY KEY,
    semester_year INT UNSIGNED NOT NULL,
    course_code VARCHAR(50) NULL,
    course_name VARCHAR(255) NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'new',
    scheme_id INT NOT NULL,
    FOREIGN KEY (scheme_id) REFERENCES feeapp_schemeofstudy(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_registeredstudent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(10) NOT NULL DEFAULT 'morning',
    college_roll_no VARCHAR(50) NULL,
    university_roll_no VARCHAR(50) NULL,
    registration_no VARCHAR(50) NULL,
    name VARCHAR(255) NOT NULL,
    cnic_no VARCHAR(20) NOT NULL UNIQUE,
    photo VARCHAR(100) NULL,
    date_of_birth DATE NOT NULL,
    mobile_no VARCHAR(15) NOT NULL,
    email VARCHAR(254) NOT NULL,
    father_name VARCHAR(255) NOT NULL,
    father_cnic VARCHAR(20) NOT NULL,
    father_mobile_no VARCHAR(15) NOT NULL,
    father_occupation VARCHAR(255) NOT NULL,
    guardian_name VARCHAR(255) NULL,
    guardian_cnic VARCHAR(20) NULL,
    guardian_contact_no VARCHAR(15) NULL,
    permanent_address LONGTEXT NOT NULL,
    postal_address LONGTEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    religion VARCHAR(50) NOT NULL,
    hafiz_e_quran TINYINT(1) NOT NULL DEFAULT 0,
    hafiz_doc VARCHAR(100) NULL,
    blood_group VARCHAR(10) NOT NULL DEFAULT 'A+',
    marital_status VARCHAR(10) NOT NULL,
    disability_status TINYINT(1) NOT NULL DEFAULT 0,
    disability_type VARCHAR(100) NULL,
    related_to_worker TINYINT(1) NOT NULL DEFAULT 0,
    worker_name VARCHAR(255) NULL,
    worker_relation VARCHAR(30) NULL,
    worker_payscale VARCHAR(50) NULL,
    worker_status TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATE NOT NULL,
    district_id INT NULL,
    province_id INT NULL,
    scheme_of_study_id INT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES feeapp_district(id) ON DELETE SET NULL,
    FOREIGN KEY (province_id) REFERENCES feeapp_province(id) ON DELETE SET NULL,
    FOREIGN KEY (scheme_of_study_id) REFERENCES feeapp_schemeofstudy(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_feehead (
    fee_head_account_id INT AUTO_INCREMENT PRIMARY KEY,
    fee_head_name VARCHAR(255) NOT NULL,
    fee_head_amount DECIMAL(10, 2) NOT NULL
);

CREATE TABLE feeapp_feeheadprogram (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fee_head_id INT NOT NULL,
    program_id INT NOT NULL,
    FOREIGN KEY (fee_head_id) REFERENCES feeapp_feehead(fee_head_account_id) ON DELETE CASCADE,
    FOREIGN KEY (program_id) REFERENCES feeapp_programs(id) ON DELETE CASCADE,
    UNIQUE (fee_head_id, program_id)
);

CREATE TABLE feeapp_logo (
    college_id INT AUTO_INCREMENT PRIMARY KEY,
    college_name VARCHAR(255) NOT NULL,
    logo_path VARCHAR(255) NULL,
    logo VARCHAR(100) NULL,
    uploaded_by VARCHAR(255) NULL,
    uploaded_date DATETIME NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE feeapp_challan (
    challan_number VARCHAR(50) PRIMARY KEY,
    due_date DATE NULL,
    challan_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'UNPAID',
    payment_status VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    original_total_amount DECIMAL(10, 2) NULL,
    remaining_amount DECIMAL(10, 2) NULL,
    download_status VARCHAR(20) NOT NULL DEFAULT 'NOT_APPLICABLE',
    challan_generation_date DATE NOT NULL,
    challan_generation_time TIME NULL,
    html_content LONGTEXT NULL,
    challan_file VARCHAR(100) NULL,
    disciplines LONGTEXT NULL,
    semesters LONGTEXT NULL,
    one_bill_number VARCHAR(50) NULL,
    created_by_clerk_id INT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY (created_by_clerk_id) REFERENCES feeapp_clerk(id) ON DELETE SET NULL,
    FOREIGN KEY (student_id) REFERENCES feeapp_registeredstudent(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_challanfeehead (
    id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    date_of_generation DATE NOT NULL,
    challan_id VARCHAR(50) NOT NULL,
    fee_head_account_id INT NOT NULL,
    FOREIGN KEY (challan_id) REFERENCES feeapp_challan(challan_number) ON DELETE CASCADE,
    FOREIGN KEY (fee_head_account_id) REFERENCES feeapp_feehead(fee_head_account_id) ON DELETE CASCADE,
    UNIQUE (fee_head_account_id, challan_id)
);

CREATE TABLE feeapp_installment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    installment_number INT UNSIGNED NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UNPAID',
    installment_challan_id VARCHAR(50) NOT NULL UNIQUE,
    original_challan_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (installment_challan_id) REFERENCES feeapp_challan(challan_number) ON DELETE CASCADE,
    FOREIGN KEY (original_challan_id) REFERENCES feeapp_challan(challan_number) ON DELETE CASCADE,
    UNIQUE (original_challan_id, installment_number)
);

CREATE TABLE feeapp_payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(100) NULL,
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    challan_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (challan_id) REFERENCES feeapp_challan(challan_number) ON DELETE CASCADE
);

CREATE TABLE feeapp_clerkotp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    otp_code VARCHAR(6) NOT NULL,
    created_at DATETIME NOT NULL,
    is_used TINYINT(1) NOT NULL DEFAULT 0,
    clerk_id INT NOT NULL,
    FOREIGN KEY (clerk_id) REFERENCES feeapp_clerk(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_clerkloginhistory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    login_time TIME NOT NULL,
    logout_time TIME NULL,
    logout_date DATE NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES feeapp_user(id) ON DELETE CASCADE
);

CREATE TABLE feeapp_clerkactivityhistory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    time TIME NOT NULL,
    first_challan_number VARCHAR(50) NULL,
    last_challan_number VARCHAR(50) NULL,
    clerk_id INT NOT NULL,
    FOREIGN KEY (clerk_id) REFERENCES feeapp_clerk(id) ON DELETE CASCADE
);

CREATE TABLE auth_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE auth_permission (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content_type_id INT NOT NULL,
    codename VARCHAR(100) NOT NULL,
    UNIQUE (content_type_id, codename)
);

CREATE TABLE auth_group_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    permission_id INT NOT NULL,
    UNIQUE (group_id, permission_id),
    FOREIGN KEY (group_id) REFERENCES auth_group(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES auth_permission(id) ON DELETE CASCADE
);

CREATE TABLE auth_user_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    UNIQUE (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES feeapp_user(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES auth_group(id) ON DELETE CASCADE
);

CREATE TABLE auth_user_user_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    UNIQUE (user_id, permission_id),
    FOREIGN KEY (user_id) REFERENCES feeapp_user(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES auth_permission(id) ON DELETE CASCADE
);

CREATE TABLE django_content_type (
    id INT AUTO_INCREMENT PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE (app_label, model)
);

CREATE TABLE django_admin_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action_time DATETIME NOT NULL,
    object_id LONGTEXT NULL,
    object_repr VARCHAR(200) NOT NULL,
    action_flag SMALLINT UNSIGNED NOT NULL,
    change_message LONGTEXT NOT NULL,
    content_type_id INT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES feeapp_user(id) ON DELETE CASCADE
);

CREATE TABLE django_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied DATETIME NOT NULL
);

CREATE INDEX feeapp_registeredstudent_cnic_idx ON feeapp_registeredstudent(cnic_no);
CREATE INDEX feeapp_registeredstudent_scheme_idx ON feeapp_registeredstudent(scheme_of_study_id);
CREATE INDEX feeapp_challan_student_idx ON feeapp_challan(student_id);
CREATE INDEX feeapp_challan_status_idx ON feeapp_challan(payment_status);
CREATE INDEX feeapp_payment_challan_idx ON feeapp_payment(challan_id);
CREATE INDEX feeapp_installment_original_idx ON feeapp_installment(original_challan_id);
CREATE INDEX django_session_expire_idx ON django_session(expire_date);