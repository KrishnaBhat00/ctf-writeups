---
title: "LA CTF 2025 Cache It To Win It"
author: "Krishna Bhat"
---

# Cache It to Win It
The challenge had a simple premise. Hit the `/check` endpoint with a given UUID parameter 100 times and you get the flag. The catch? Requests are cached so that the counter does not update on repeated requests. 

The application gives users uuids and places them into a database. Every time a user visits the `/check` endpoint, if the uuid is in the database its counter is increased until it reaches 100 and releases the flag. The uuids are in the form of `23c16f81-5868-41b6-bc2f-42aec0dedf56`. The app is written in Python with Flask and uses mariadb, a SQL like database, on the backend. 

In order to increase the counter we need to dodge the cache while submitting the same UUID.

## Problem
### Caches
Caches are an optimization technique where instead of processing every request, the server will serve the same response to similar requests. When a server receives a request, before running the associated code, it will check the cache key to determine if it can send a previous response back. In this case, the key is basically just the user's uuid. This prevents the counter from decreasing because subsequent requests are not processed by the `check()` function. 


The way they compare UUIDs in the database as follows:
```python
user_uuid = request.args.get("uuid")
if not user_uuid:
    return {"error": "UUID parameter is required"}, 400

run_query("UPDATE users SET value = value + 1 WHERE id = %s;", (user_uuid,))
res = run_query("SELECT * FROM users WHERE id = %s;", (user_uuid,))
```
And the cache comparison looks like this:
```python
def normalize_uuid(uuid: str):
    uuid_l = list(uuid)
    i = 0
    for i in range(len(uuid)):
        uuid_l[i] = uuid_l[i].upper()
        if uuid_l[i] == "-":
            uuid_l.pop(i)
            uuid_l.append(" ")

    return "".join(uuid_l)

def make_cache_key():
    return f"GET_check_uuids:{normalize_uuid(request.args.get('uuid'))}"[:64]  # prevent spammers from filling redis cache
```

The database uses the UUID straight from the URI parameter, while the cache key uses the `normalize_uuid` function.
Weirdly enough instead of replacing all instances of `"-"` with `" "`, it pops the former from the list and appends the later to the end, and because of this it skips the character. 

## Solution
The key to this challenge is that the database has very loose matching requirements. For example, matching letters is case insensitive, meaning `'a' = 'A'` to mariadb (and many other SQL languages). We can not solve the challenge with this because `normalize_uuid()` calls `.upper()` on every character (we could do this with characters next to `-` because of the error mentioned above but this will only give us 2^3 variations if we get a uuid with letters next to the dashes). 

That being said, there are other aspects where the database is not strict about comparisons. There are many Unicode characters which alter previous characters. These include `\u0308` and `\u20DE` which look like `ä` and `a⃞` respectively. These characters are interpreted by python's cache key comparison as different, but ignored by mariadb. By adding a number of these to the letters in the uuid, we can create variations which create cache misses and pass the database look up. With enough Unicode characters and enough letters in the UUID, we can create more than enough variations. 