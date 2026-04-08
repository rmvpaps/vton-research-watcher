from shared import create_tables,create_database,delete_database
import asyncio

async def main():
    await delete_database()
    print("Deleted Project DB")
    await create_database()
    print("Created new Project DB")
    await create_tables()
    print("Basic tables created succesfully")


if __name__ == "__main__":
    asyncio.run(main())