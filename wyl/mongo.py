import asyncio
import json
import time
from pprint import pformat, pprint
import uuid
import motor.motor_asyncio
from wyl.time import Time

user_key = ""
user_id_key = 0

client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
db = client.test


async def get_latest_weather():
    documents = []
    cursor = db.weatherData.find()

    times = {}
    for document in await cursor.to_list(length=100):
        documents.append(document)
        uuid_ = None
        for k in document.keys():
            if k != "_id":
                uuid_ = k
        if uuid_ is not None:
            seconds_ = int(time.time() - document[uuid_]["t"])
            # print(str(seconds_)+" seconds")
            #print(Time().display_time(seconds_))
            times[uuid_] = seconds_

    # print(times)
    return times, documents


async def do_insert_weather(data):
    global user_id_key
    current_uuid = str(uuid.uuid4())
    document = {current_uuid: {
        "data": data,
        "t": time.time()
    }}

    result = await db.weatherData.insert_one(document)
    # print('result %s' % repr(result.inserted_id))
    return current_uuid, result.inserted_id


async def do_insert(key, value):
    global user_id_key
    document = {str(key): value}
    user_id_key = key
    result = await db.posts.insert_one(document)
    # print('result %s' % repr(result.inserted_id))
    return result.inserted_id


async def do_update_entry(user_id_key, data):
    # print(data)
    coll = db.posts
    current_documents = coll.find( {} )
    # print(current_documents)
    exists = False
    doc_  = None
    async for document in current_documents:
        if str(user_id_key) in document.keys():
            doc_ = document
            exists = True
            break
    if exists:
        if data.keys() == doc_[user_id_key].keys():
            document_id = doc_["_id"]
            # print(document_id)
            result = await coll.update_one({'_id':  doc_["_id"]}, {'$set': {"" + user_id_key + "": data}})
            # print('updated %s document' % result.modified_count)
            new_document = await coll.find_one({'_id':  doc_["_id"]})
            # print('document is now %s' % pformat(new_document))
    else:
        print("does not exist: "+str(user_id_key)+" target-data: "+json.dumps(data))


async def do_update(doc_id, user_key, data):
    coll = db.posts
    current_document = await coll.find_one({'_id': user_key})
    # print("cur")
    # print(current_document)

    result = await coll.update_one({'_id': doc_id}, {'$set': {""+user_key+"": data}})
    print('updated %s document' % result.modified_count)
    new_document = await coll.find_one({'_id': doc_id})
    print('document is now %s' % pformat(new_document))
    return result.modified_count


async def do_find(search_dict):
    documents = []
    cursor = db.posts.find(search_dict)
    for document in await cursor.to_list(length=100):
        documents.append(document)
    return documents


def find_some(search_dict):
    updated = asyncio.create_task(do_find(search_dict))
    return updated


def insert_object(key):
    global user_key
    loop = asyncio.get_event_loop()
#    loop.run_until_complete(do_find())
    inserted = asyncio.create_task(do_insert(key, {"lat": 0, "lon": 0}))
    # inserted = loop.run_until_complete(do_insert(key, {"lat": 0, "lon": 0}))
    print("inserted: " + str(inserted))
    user_key = inserted


def update_object(docid, user_id, lat, lon):
    lat_ = float(lat)
    lon_ = float(lon)
    updated = asyncio.create_task(do_update(docid, user_id, {"lat": lat_, "lon": lon_}))
    # print(updated)
    return updated
