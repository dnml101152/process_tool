from pymongo import MongoClient

# Replace with your actual URI and credentials
uri = "mongodb+srv://testuser:MetaplanetDN3@booknotes.7kpvxmc.mongodb.net/?retryWrites=true&w=majority&appName=booknotes"

# Connect to MongoDB Atlas
client = MongoClient(uri)

# Access your database and collection
db = client["booknotes"]
collection = db["sources"]

# Example operation: print all documents
for doc in collection.find():
    print(doc)


from pymongo import MongoClient
from pymongo.errors import BulkWriteError

# === CONFIGURATION ===
# Local MongoDB
local_uri = "mongodb://localhost:27017"
local_db_name = "booknotes"
local_collection_name = "tags"

# MongoDB Atlas
atlas_uri = "mongodb+srv://testuser:MetaplanetDN3@booknotes.7kpvxmc.mongodb.net/?retryWrites=true&w=majority&appName=booknotes"
atlas_db_name = "booknotes"
atlas_collection_name = "tags"

# Optional: clear the Atlas collection before inserting
clear_target_collection_first = False
# =======================

# Connect to local MongoDB
local_client = MongoClient(local_uri)
local_db = local_client[local_db_name]
local_collection = local_db[local_collection_name]

# Connect to MongoDB Atlas
atlas_client = MongoClient(atlas_uri)
atlas_db = atlas_client[atlas_db_name]
atlas_collection = atlas_db[atlas_collection_name]

# Optional: Clear the Atlas collection before copying
if clear_target_collection_first:
    delete_result = atlas_collection.delete_many({})
    print(f"🗑️  Cleared {delete_result.deleted_count} documents from Atlas collection.")

# Fetch all documents from local MongoDB
documents = list(local_collection.find())

if documents:
    try:
        result = atlas_collection.insert_many(documents, ordered=False)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} documents into Atlas.")
    except BulkWriteError as bwe:
        print("⚠️ Some documents failed to insert due to duplicate _id values.")
        for error in bwe.details["writeErrors"]:
            print(f" - Error at index {error['index']}: {error['errmsg']}")
else:
    print("ℹ️ No documents found in the local collection.")