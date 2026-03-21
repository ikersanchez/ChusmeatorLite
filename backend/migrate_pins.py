from sqlalchemy import create_engine, text

def migrate():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/chusmeator")
    with engine.begin() as conn:
        print("Adding 'color' column to 'pins' table...")
        try:
            conn.execute(text("ALTER TABLE pins ADD COLUMN color VARCHAR(10) NOT NULL DEFAULT 'blue';"))
            print("Successfully added 'color' column.")
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    migrate()
