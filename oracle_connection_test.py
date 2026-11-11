--Connection test that works fine

import getpass
import oracledb

username = input("Oracle username: ")
password = getpass.getpass("Oracle password: ")
dsn = input("Oracle connection string or alias: ")

query = """
    SELECT g.greenspace_id, g.site_name, c.carbon_stock_kg_carbon
    FROM cgs_greenspace g
    LEFT JOIN cgs_site_carbon c
        ON g.greenspace_id = c.greenspace_id
    ORDER BY g.greenspace_id
"""

try:
    with oracledb.connect(user=username, password=password, dsn=dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            print("\nGreenspace results:")
            for row in cursor:
                print(row)

except oracledb.Error as error:
    print("Oracle connection or query failed:", error)
