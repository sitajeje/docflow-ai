
from backend.app.db.models import Base
from backend.app.db.session import engine


def main():
    Base.metadata.create_all(bind=engine)
    print("DocFlow AI tables initialized.")


if __name__ == "__main__":
    main()
