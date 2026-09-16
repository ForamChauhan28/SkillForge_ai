import mysql.connector
from mysql.connector import pooling, Error
from config import Config


# Connection pool for efficient database access
_pool = None


def get_pool():
    """Get or create the MySQL connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="skillforge_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
        except Error as e:
            print(f"Error creating connection pool: {e}")
            raise
    return _pool


def get_connection():
    """Get a connection from the pool."""
    try:
        return get_pool().get_connection()
    except Exception as e:
        print(f"[ERROR] Could not get database connection: {e}")
        return None


def init_database():
    """Create the database and all required tables if they don't exist."""
    # First connect without specifying database to create it
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(f"USE `{Config.MYSQL_DATABASE}`")

        # ── Table: users ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        # ── Table: user_profiles ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                profile_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                extracted_skills TEXT,
                dream_job VARCHAR(150),
                resume_filename VARCHAR(255),
                resume_text LONGTEXT,
                ats_score_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        # ── Table: roadmaps ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roadmaps (
                roadmap_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                raw_json JSON,
                certifications_json JSON,
                projects_json JSON,
                interview_json JSON,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        # ── Table: roadmap_nodes ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roadmap_nodes (
                node_id INT AUTO_INCREMENT PRIMARY KEY,
                roadmap_id INT NOT NULL,
                phase_id INT NOT NULL,
                topic_name VARCHAR(150) NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (roadmap_id) REFERENCES roadmaps(roadmap_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        # ── Table: mock_interviews ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_interviews (
                session_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role_title VARCHAR(150) NOT NULL,
                target_company VARCHAR(150) DEFAULT 'General',
                round_type VARCHAR(50) NOT NULL,
                total_questions INT DEFAULT 5,
                current_question_index INT DEFAULT 0,
                status ENUM('in_progress', 'completed') DEFAULT 'in_progress',
                overall_score FLOAT DEFAULT NULL,
                report_json JSON DEFAULT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        # ── Table: mock_interview_qa ──
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_interview_qa (
                qa_id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                question_index INT NOT NULL,
                question_text TEXT NOT NULL,
                category VARCHAR(50) DEFAULT 'general',
                difficulty VARCHAR(20) DEFAULT 'medium',
                user_answer TEXT DEFAULT NULL,
                feedback_json JSON DEFAULT NULL,
                score FLOAT DEFAULT NULL,
                answered_at TIMESTAMP NULL,
                FOREIGN KEY (session_id) REFERENCES mock_interviews(session_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        conn.commit()

        # Migrate existing tables - add new columns if they don't exist
        migrations = [
            ("user_profiles", "resume_text", "ALTER TABLE user_profiles ADD COLUMN resume_text LONGTEXT AFTER resume_filename"),
            ("user_profiles", "ats_score_json", "ALTER TABLE user_profiles ADD COLUMN ats_score_json TEXT AFTER resume_text"),
        ]

        cursor = conn.cursor()
        for table, column, sql in migrations:
            try:
                cursor.execute(f"SELECT {column} FROM {table} LIMIT 0")
            except Exception:
                try:
                    cursor.execute(sql)
                    conn.commit()
                    print(f"[OK] Added column {column} to {table}")
                except Exception as me:
                    print(f"[INFO] Migration note for {table}.{column}: {me}")

        cursor.close()
        conn.close()
        print("[OK] Database and tables initialized successfully!")

    except Error as e:
        print(f"[ERROR] Database initialization error: {e}")
        raise
