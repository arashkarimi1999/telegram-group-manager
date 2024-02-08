from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from os import getenv

class DBHandler:
    def __init__(self):
        self.client = MongoClient(getenv("uri"), server_api=ServerApi('1'))
        print(type(getenv("db_name")), getenv("db_name"))
        self.db = self.client[getenv("db_name")]

    def check_connection(self):
        try:
            self.client.admin.command("ping")
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    def insert_one(self, collection_name, data):
        result = self.db[collection_name].insert_one(data)
        return result.inserted_id

    def find(self, collection_name, query, sort=False):
        result = self.db[collection_name].find(query)
        if sort:
            result = result.sort(sort)
        return list(result)

    def update_many(self, collection_name, query, update):
        result = self.db[collection_name].update_many(query, update)
        return result.modified_count

    def delete_many(self, collection_name, query):
        result = self.db[collection_name].delete_many(query)
        return result.deleted_count

    def random_choose(self, collection_name, size=1):
        random_rows = self.db[collection_name].aggregate([{"$sample": {"size": size}}])
        return list(random_rows)

mongo = DBHandler()